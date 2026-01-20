#!/usr/bin/env python3
"""
Stremio API Library Extractor
This script uses the Stremio API to extract library data and create watched/watchlist CSVs
"""

import asyncio
import requests
import csv
import json
import logging
from pathlib import Path
from datetime import datetime
import webbrowser
import zipfile
from auth_extractor import extract_stremio_auth_key
from html_generator import generate_html


def setup_logging():
    """Setup structured logging with timestamps"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger(__name__)


def make_api_request(auth_key, logger):
    """Make POST request to Stremio API to get library data"""
    url = "https://api.strem.io/api/datastoreGet"
    
    payload = {
        "all": True,
        "authKey": auth_key,
        "collection": "libraryItem"
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    logger.info("Making API request to Stremio datastore")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"API request successful - received {len(data.get('result', []))} items")
        return data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse API response: {e}")
        raise


def parse_library_data(api_response, logger):
    """Parse API response and categorize into watched/watchlist"""
    result = api_response.get('result', [])
    
    watched_items = []
    watchlist_items = []
    
    for item in result:
        # Extract required fields
        imdb_id = item.get('_id', '')
        name = item.get('name', '')
        state = item.get('state', {})
        flagged_watched = state.get('timesWatched', 0)
        
        # Extract additional fields for HTML export
        poster = item.get('poster')
        if not poster and 'meta' in item and 'poster' in item['meta']:
             poster = item['meta']['poster']
             
        year = item.get('year')
        if not year and 'meta' in item:
            year = item['meta'].get('year')
            
        item_type = item.get('type', 'movie')
        
        # Skip items without essential data
        if not imdb_id or not name:
            continue
            
        movie_data = {
            'imdbID': imdb_id, 
            'Title': name,
            'poster': poster,
            'year': year,
            'type': item_type
        }
        
        # Categorize based on flaggedWatched field
        if flagged_watched > 0:
            watched_items.append(movie_data)
        else:
            watchlist_items.append(movie_data)
    
    logger.info(f"Parsed {len(watched_items)} watched items and {len(watchlist_items)} watchlist items")
    return watched_items, watchlist_items


def save_to_csv(items, filename, logger):
    """Save items to CSV file with extended headers"""
    if not items:
        logger.warning(f"No items to save for {filename}")
        return
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['imdbID', 'Title', 'year', 'type', 'poster']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
        
        writer.writeheader()
        for item in items:
            writer.writerow(item)
    
    logger.info(f"Saved {len(items)} items to {filename}")


def save_json_backup(data, filename, logger):
    """Save raw API response to JSON file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved raw library backup to {filename}")
    except Exception as e:
        logger.error(f"Failed to save JSON backup: {e}")


def create_backup_zip(output_dir, timestamp, logger):
    """Create a ZIP archive of the exported files"""
    zip_filename = output_dir / f"stremio_library_backup_{timestamp}.zip"
    
    try:
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add all files created in this session
            # We look for files with the same timestamp
            for file_path in output_dir.glob(f"*{timestamp}*"):
                if file_path.suffix != '.zip':
                    zipf.write(file_path, arcname=file_path.name)
            
            # Also add the static raw backup if it exists (renaming it with timestamp)
            raw_backup = output_dir / "library_backup.json"
            if raw_backup.exists():
                zipf.write(raw_backup, arcname=f"library_backup_{timestamp}.json")
                
        logger.info(f"📦 Created backup archive: {zip_filename}")
        return zip_filename
    except Exception as e:
        logger.error(f"Failed to create ZIP archive: {e}")
        return None


async def main():
    """Main function to extract library data and create CSVs"""
    logger = setup_logging()
    
    try:
        # Step 1: Extract auth key
        logger.info("🔑 Extracting Stremio auth key...")
        auth_key = await extract_stremio_auth_key(headless=True)
        logger.info(f"Auth key extracted: {auth_key[:20]}...")
        
        # Step 2: Make API request
        logger.info("📡 Fetching library data from Stremio API...")
        api_response = make_api_request(auth_key, logger)
        
        # Step 3: Parse the data
        logger.info("📊 Parsing library data...")
        watched_items, watchlist_items = parse_library_data(api_response, logger)
        
        # Step 4: Create output directory and filenames
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        watched_csv = output_dir / f"watched_api_{timestamp}.csv"
        watchlist_csv = output_dir / f"watchlist_api_{timestamp}.csv"
        
        # Step 5: Save to CSV files
        logger.info("💾 Saving to CSV files...")
        save_to_csv(watched_items, watched_csv, logger)
        save_to_csv(watchlist_items, watchlist_csv, logger)
        
        # Step 6: Generate HTML export
        logger.info("🎨 Generating HTML export...")
        html_file = output_dir / f"stremio_library_{timestamp}.html"
        generate_html(watched_items, watchlist_items, html_file)
        
        # Step 7: Save raw JSON backup
        logger.info("💾 Saving raw JSON backup...")
        json_backup_path = output_dir / "library_backup.json"
        save_json_backup(api_response, json_backup_path, logger)
        
        # Step 8: Create ZIP archive
        logger.info("📦 Creating ZIP archive...")
        zip_file = create_backup_zip(output_dir, timestamp, logger)
        
        # Step 9: Display summary
        logger.info("✅ Library extraction completed successfully!")
        logger.info(f"📄 Watched movies saved to: {watched_csv}")
        logger.info(f"📄 Watchlist movies saved to: {watchlist_csv}")
        logger.info(f"🖼️  HTML export saved to: {html_file}")
        if zip_file:
            logger.info(f"🗄️  Backup ZIP saved to: {zip_file}")
        
        # Open the HTML file in default browser
        logger.info("🚀 Opening HTML report...")
        webbrowser.open(html_file.absolute().as_uri())
        
        # Display previews
        if watched_items:
            logger.info(f"\n🎬 First {min(5, len(watched_items))} watched movies:")
            for i, item in enumerate(watched_items[:5], 1):
                logger.info(f"  {i:2d}. {item['Title']} ({item['imdbID']})")
            if len(watched_items) > 5:
                logger.info(f"  ... and {len(watched_items) - 5} more")
        
        if watchlist_items:
            logger.info(f"\n📋 First {min(5, len(watchlist_items))} watchlist movies:")
            for i, item in enumerate(watchlist_items[:5], 1):
                logger.info(f"  {i:2d}. {item['Title']} ({item['imdbID']})")
            if len(watchlist_items) > 5:
                logger.info(f"  ... and {len(watchlist_items) - 5} more")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Library extraction failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
