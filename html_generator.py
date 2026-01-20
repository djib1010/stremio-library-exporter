
import json
import logging
from pathlib import Path
from datetime import datetime

def generate_html(watched_items, watchlist_items, output_path):
    """
    Generate a beautiful HTML file for the library export.
    """
    logger = logging.getLogger(__name__)
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stremio Library Export</title>
    <style>
        :root {{
            --bg-color: #121212;
            --card-bg: #1e1e1e;
            --text-color: #e0e0e0;
            --accent-color: #6c5ce7;
            --secondary-text: #a0a0a0;
        }}
        
        body {{
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            padding: 20px;
        }}
        
        header {{
            text-align: center;
            margin-bottom: 40px;
            padding: 20px 0;
            border-bottom: 1px solid #333;
        }}
        
        h1 {{
            color: var(--accent-color);
            margin-bottom: 10px;
        }}
        
        .stats {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .stat-box {{
            background: var(--card-bg);
            padding: 10px 20px;
            border-radius: 8px;
            text-align: center;
        }}
        
        .stat-number {{
            display: block;
            font-size: 1.5em;
            font-weight: bold;
            color: var(--accent-color);
        }}
        
        .tabs {{
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-bottom: 30px;
        }}
        
        .tab-btn {{
            background: var(--card-bg);
            border: none;
            color: var(--text-color);
            padding: 10px 25px;
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 1em;
        }}
        
        .tab-btn.active {{
            background: var(--accent-color);
            color: white;
        }}
        
        .tab-btn:hover:not(.active) {{
            background: #2d2d2d;
        }}
        
        .search-container {{
            text-align: center;
            margin-bottom: 30px;
        }}
        
        #search-input {{
            padding: 10px 15px;
            width: 300px;
            border-radius: 20px;
            border: 1px solid #333;
            background: var(--card-bg);
            color: var(--text-color);
            font-size: 1em;
        }}
        
        .grid-container {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 25px;
            padding: 0 20px;
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .movie-card {{
            background: var(--card-bg);
            border-radius: 10px;
            overflow: hidden;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            position: relative;
            height: 100%;
            display: flex;
            flex-direction: column;
        }}
        
        .movie-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.3);
        }}
        
        .poster-container {{
            position: relative;
            padding-top: 150%; /* 2:3 aspect ratio */
            background-color: #2a2a2a;
            overflow: hidden;
        }}
        
        .poster-img {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.3s ease;
        }}
        
        .movie-card:hover .poster-img {{
            transform: scale(1.05);
        }}
        
        .card-content {{
            padding: 15px;
            flex-grow: 1;
            display: flex;
            flex-direction: column;
        }}
        
        .movie-title {{
            font-size: 1.1em;
            margin: 0 0 5px 0;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        
        .movie-meta {{
            font-size: 0.9em;
            color: var(--secondary-text);
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
        }}
        
        .type-badge {{
            background: #333;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            text-transform: uppercase;
        }}
        
        .links {{
            margin-top: auto;
            text-align: right;
        }}
        
        .imdb-link {{
            color: #f5c518;
            text-decoration: none;
            font-size: 0.9em;
        }}
        
        .section {{
            display: none;
        }}
        
        .section.active {{
            display: block;
            animation: fadeIn 0.5s ease;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        
        .fallback-poster {{
            display: flex;
            align-items: center;
            justify-content: center;
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            color: #555;
            font-size: 3em;
            background: #2a2a2a;
        }}
    </style>
</head>
<body>
    <header>
        <h1>Stremio Library Export</h1>
        <p>Generated on {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
        
        <div class="stats">
            <div class="stat-box">
                <span class="stat-number">{len(watched_items)}</span>
                Watched
            </div>
            <div class="stat-box">
                <span class="stat-number">{len(watchlist_items)}</span>
                Watchlist
            </div>
        </div>
    </header>
    
    <div class="search-container">
        <input type="text" id="search-input" placeholder="Search by title..." onkeyup="filterMovies()">
    </div>
    
    <div class="tabs">
        <button class="tab-btn active" onclick="switchTab('watched')">Watched</button>
        <button class="tab-btn" onclick="switchTab('watchlist')">Watchlist</button>
        <button class="tab-btn" onclick="switchTab('backup')">Backup & Restore</button>
    </div>
    
    <div id="watched" class="section active">
        <div class="grid-container">
            {_generate_grid_items(watched_items)}
        </div>
    </div>
    
    <div id="watchlist" class="section">
        <div class="grid-container">
            {_generate_grid_items(watchlist_items)}
        </div>
    </div>

    <div id="backup" class="section">
        <div style="max-width: 800px; margin: 0 auto; color: var(--text-color); background: var(--card-bg); padding: 30px; border-radius: 10px;">
            <h2 style="color: var(--accent-color); border-bottom: 1px solid #333; padding-bottom: 15px;">Backup & Restore</h2>
            
            <h3>📦 Backup Contents</h3>
            <p>Your export folder contains a ZIP file named <code>stremio_library_backup_TIMESTAMP.zip</code>. This archive includes:</p>
            <ul style="line-height: 1.6;">
                <li><strong>HTML Report</strong>: This visual gallery.</li>
                <li><strong>CSV Files</strong>: Specific lists for watched movies and watchlist.</li>
                <li><strong>library_backup.json</strong>: The raw data needed for restoration.</li>
            </ul>
            
            <h3 style="margin-top: 30px;">♻️ How to Restore</h3>
            <p>To import this library into a new Stremio account (or restore to an existing one), follow these steps:</p>
            <ol style="line-height: 1.6;">
                <li>Unzip the backup file.</li>
                <li>Make sure you have Python installed.</li>
                <li>Run the importer tool from the command line:</li>
            </ol>
            <pre style="background: #000; padding: 15px; border-radius: 5px; overflow-x: auto;"><code>python library_importer.py library_backup.json</code></pre>
            <p><em>Note: You will be asked to log in to the destination account.</em></p>
        </div>
    </div>

    <script>
        function switchTab(tabName) {{
            // Hide all sections
            document.querySelectorAll('.section').forEach(el => {{
                el.classList.remove('active');
            }});
            
            // Show new section
            document.getElementById(tabName).classList.add('active');
            
            // Update buttons
            document.querySelectorAll('.tab-btn').forEach(btn => {{
                btn.classList.remove('active');
            }});
            event.target.classList.add('active');
        }}
        
        function filterMovies() {{
            const input = document.getElementById('search-input');
            const filter = input.value.toLowerCase();
            const cards = document.querySelectorAll('.movie-card');
            
            cards.forEach(card => {{
                const title = card.getAttribute('data-title').toLowerCase();
                if (title.indexOf(filter) > -1) {{
                    card.style.display = "";
                }} else {{
                    card.style.display = "none";
                }}
            }});
        }}
    </script>
</body>
</html>
    """
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"HTML export generated successfully at {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to generate HTML export: {e}")
        return False

def _generate_grid_items(items):
    html = ""
    for item in items:
        poster = item.get('poster')
        title = item.get('Title', 'Unknown')
        year = item.get('year', '')
        imdb_id = item.get('imdbID', '')
        type_ = item.get('type', 'movie')
        
        poster_html = ""
        if poster:
            poster_html = f'<img src="{poster}" class="poster-img" alt="{title}" onerror="this.style.display=\'none\'; this.nextElementSibling.style.display=\'flex\'">'
            poster_html += f'<div class="fallback-poster" style="display:none"><span>🎬</span></div>'
        else:
            poster_html = f'<div class="fallback-poster"><span>🎬</span></div>'
            
        html += f"""
        <div class="movie-card" data-title="{title}">
            <div class="poster-container">
                {poster_html}
            </div>
            <div class="card-content">
                <h3 class="movie-title" title="{title}">{title}</h3>
                <div class="movie-meta">
                    <span>{year}</span>
                    <span class="type-badge">{type_}</span>
                </div>
                <div class="links">
                    <a href="https://www.imdb.com/title/{imdb_id}" target="_blank" class="imdb-link">IMDb ↗</a>
                </div>
            </div>
        </div>
        """
    return html

if __name__ == "__main__":
    # Test with dummy data
    logging.basicConfig(level=logging.INFO)
    dummy_watched = [{'Title': 'Test Movie', 'imdbID': 'tt1234567', 'year': '2023', 'type': 'movie', 'poster': 'https://image.tmdb.org/t/p/w500/1E5baAaEse26fej7uHcjOgEE2t2.jpg'}]
    dummy_watchlist = [{'Title': 'Test Series', 'imdbID': 'tt7654321', 'year': '2024', 'type': 'series'}]
    generate_html(dummy_watched, dummy_watchlist, "test_output.html")
