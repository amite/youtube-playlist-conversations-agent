YouTube Playlist to CSV Database - Complete Summary

### Project Overview
This project demonstrates how to extract complete data from any YouTube playlist and generate a properly formatted CSV database with the following columns:

```
video_id: YouTube video ID
title: Video title
video_description: Full video description
video_length: Duration in ISO 8601 format (PT1H2M3S)
video_published_datetime: Exact timestamp when published
video_likes: Like count
video_views: View count
number_comments: Comment count
```

The project uses the YouTube Data API v3 to fetch playlist data and was implemented using two approaches: Browser Console JavaScript and Python Playwright Automation.

### Quick Start

Option 1: Browser Console (Fastest)

Go to your YouTube playlist
Press F12 or Ctrl+Shift+J to open Developer Console
Go to Console tab
Paste and run the JavaScript script (see below)
File downloads automatically as youtube_playlist.csv

Option 2: Python with uv (Most Reliable)

```bash
# Create project
mkdir youtube_playlist_scraper
cd youtube_playlist_scraper

# Create pyproject.toml (see template below)
# Create scraper.py (see code below)

# Install and run
uv sync
uv run playwright install
uv run python scraper.py PLAYLIST_ID  # Replace PLAYLIST_ID with your actual playlist ID e,g, PL15F8EFEA8777D0C6
```

---

## Setup: Google Cloud & API Key

### Step 1: Create Google Cloud Project
1. Go to https://console.cloud.google.com
2. Create new project named "scraper-agent-project"
3. Enable YouTube Data API v3 in the project
4. Create an API Key in Credentials section

### Step 2: Your API Key
```
(see .env)
```

Step 3: Get Your Playlist ID
From YouTube URL: https://www.youtube.com/playlist?list=**********
The ID is everything after list=

Solution 1: JavaScript Browser Console Script
Perfect for one-time use with no installation required.
How to Use:

Navigate to your YouTube playlist
Press F12 → Click Console tab
Copy and paste the script below
Press Enter
Watch progress in console, file auto-downloads

### Solution 2: Python Playwright Script

Better for automation and recurring tasks.
Prerequisites:

Python 3.9+
uv package manager

File 1: pyproject.toml

```toml
[project]
name = "youtube-playlist-scraper"
version = "0.1.0"
description = "Download YouTube playlist data as CSV"
requires-python = ">=3.9"
dependencies = [
    "ipykernel>=6.31.0",
    "numpy>=2.0.2",
    "pandas>=2.3.3",
    "playwright>=1.40.0",
    "python-dotenv>=1.0.0",
    "typer>=0.9.0",
]

[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"

[tool.setuptools]
py-modules = ["scraper"]
```

### Installation and usage
  
# One-time setup
uv sync
uv run playwright install

# Run the scraper with Typer CLI
uv run python scraper.py PLAYLIST_ID  # Replace PLAYLIST_ID with your actual playlist ID

# Get help
uv run python scraper.py --help

#### Key Learnings & Important Notes
1. Description Formatting

Python String Escaping Issue: Use "\\n" (single backslash) not "\\\\n" (double backslash) to match actual newline characters
Descriptions with newlines should be flattened to single lines for better NLP/vector database compatibility
The corrected Python line: snippet.get("description", "").replace("\\n", " ")

2. CSV Formatting (RFC 4180 Compliance)

All text fields must be quoted: "field1","field2"
Quotes within fields must be escaped by doubling: "He said ""hello"""
This prevents parsing issues when descriptions contain commas or special characters

3. Vector Database Optimization

Single-line descriptions are better for embedding models and NLP
Continuous text without newlines produces more consistent embeddings
Reduces token count and improves semantic understanding

4. Reusability
  
Both scripts work for any public YouTube playlist
Just provide the PLAYLIST_ID as a CLI argument
API key is unlimited for public playlists

5. Browser Console JavaScript

Works immediately in any browser with no installation
Best for one-time extractions
Handles file download gracefully
Perfect for testing and quick exports

6. Python Playwright
  
More robust for automation
Better for scheduled/recurring tasks
Easier to integrate into applications
Can process multiple playlists programmatically

7. Typer CLI Interface

User-friendly command line interface
Automatic help generation with --help
Required argument validation
Easy to extend with additional options

#### Troubleshooting

Problem Solution"API key not valid"Verify API key and YouTube Data API v3 is enabledDescriptions still have newlinesUse single backslash: "\\n" not "\\\\n"Playwright install failsRun: 

```bash
uv run playwright install --with-deps
```

File won't download (JS)Try different browser or check popup blocker"Playlist not found"Ensure playlist ID is correct and playlist is public

Use Cases
✅ Vector Database Ingestion: Feed descriptions into Pinecone/Weaviate for semantic search
✅ Data Analysis: Analyze video performance trends
✅ Content Management: Maintain organized database of playlists
✅ Research: Extract data for academic studies
✅ Automation: Schedule regular exports of playlist data
✅ Integration: Import into your own applications