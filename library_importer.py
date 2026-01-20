#!/usr/bin/env python3
"""
Stremio Library Importer
Restores a Stremio library from a JSON backup using the Stremio API.
"""

import argparse
import asyncio
import json
import logging
import requests
from pathlib import Path
from auth_extractor import extract_stremio_auth_key

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger(__name__)

def load_backup(filepath):
    """Load library backup from JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Handle both raw API response structure and direct list
        if isinstance(data, dict) and "result" in data:
            return data["result"]
        elif isinstance(data, list):
            return data
        else:
            raise ValueError("Invalid backup format. Expected list or API response dict.")
            
    except Exception as e:
        raise ValueError(f"Failed to load backup: {e}")

def restore_library(auth_key, items, logger):
    """Restore items to Stremio library using datastorePut"""
    url = "https://api.strem.io/api/datastorePut"
    
    # Process items in batches to avoid overwhelming the API
    # Note: Stremio API datastorePut typically accepts a 'changes' array
    # Format: [{"_id": "...", "name": "...", ...}, ...]
    
    batch_size = 50
    total_items = len(items)
    success_count = 0
    
    logger.info(f"Starting restore of {total_items} items...")
    
    for i in range(0, total_items, batch_size):
        batch = items[i:i + batch_size]
        
        payload = {
            "authKey": auth_key,
            "collection": "libraryItem",
            "changes": batch
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if result.get("result") == "ok" or result.get("success") == True:
                success_count += len(batch)
                logger.info(f"Restored items {i+1}-{min(i+len(batch), total_items)} of {total_items}")
            else:
                logger.warning(f"Batch {i//batch_size + 1} may have failed: {result}")
                
        except Exception as e:
            logger.error(f"Failed to restore batch starting at index {i}: {e}")
            
    return success_count

async def main():
    parser = argparse.ArgumentParser(description="Stremio Library Importer")
    parser.add_argument("backup_file", help="Path to the JSON backup file (library_backup.json)")
    args = parser.parse_args()
    
    logger = setup_logging()
    
    if not Path(args.backup_file).exists():
        logger.error(f"Backup file not found: {args.backup_file}")
        return 1
        
    try:
        # Load backup
        logger.info(f"Loading backup from {args.backup_file}...")
        items = load_backup(args.backup_file)
        logger.info(f"Loaded {len(items)} items from backup")
        
        # Get Auth Key
        logger.info("Keys needed! Logging in to Stremio...")
        auth_key = await extract_stremio_auth_key(headless=True)
        logger.info("Authentication successful")
        
        # Restore
        restored = restore_library(auth_key, items, logger)
        logger.info(f"🎉 Restore completed! Successfully restored {restored}/{len(items)} items.")
        
    except Exception as e:
        logger.error(f"❌ Restore failed: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
