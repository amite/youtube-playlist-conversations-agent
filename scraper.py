import asyncio
import csv
from pathlib import Path
from playwright.async_api import async_playwright
import json
from datetime import datetime
import os
from dotenv import load_dotenv
import typer


class YouTubePlaylistScraper:
    def __init__(self, playlist_id: str, api_key: str, output_filename: str | None = None):
        """
        Initialize the YouTube playlist scraper.
        
        Args:
            playlist_id: YouTube playlist ID (from URL: list=PLAYLIST_ID)
            api_key: YouTube Data API key
            output_filename: Optional custom output filename
        """
        self.playlist_id = playlist_id
        self.api_key = api_key
        self.output_filename = output_filename or f"playlist_{playlist_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self.base_url = "https://www.googleapis.com/youtube/v3"
        
    async def fetch_playlist_items(self):
        """Fetch all items from the playlist using YouTube API."""
        print(f"📥 Fetching playlist items for: {self.playlist_id}")
        
        all_items = []
        page_token = None
        page_count = 0
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                while True:
                    url = f"{self.base_url}/playlistItems?part=snippet,contentDetails&playlistId={self.playlist_id}&maxResults=50&key={self.api_key}"
                    if page_token:
                        url += f"&pageToken={page_token}"
                    
                    # Navigate to API endpoint to fetch JSON
                    await page.goto(url)
                    content = await page.content()
                    
                    # Extract JSON from page
                    data = json.loads(await page.evaluate("() => document.body.innerText"))
                    
                    if "error" in data:
                        print(f"❌ API Error: {data['error']['message']}")
                        return None
                    
                    all_items.extend(data.get("items", []))
                    page_count += 1
                    print(f"  ✓ Page {page_count}: {len(all_items)} items total")
                    
                    if "nextPageToken" not in data:
                        break
                    
                    page_token = data["nextPageToken"]
                
                print(f"✅ Fetched {len(all_items)} playlist items")
                return all_items
                
            finally:
                await context.close()
                await browser.close()
    
    async def fetch_video_stats(self, video_ids: list[str]):
        """Fetch statistics for videos in batches."""
        print(f"📊 Fetching video statistics for {len(video_ids)} videos...")
        
        all_videos = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Process in batches of 50 (YouTube API limit)
                for i in range(0, len(video_ids), 50):
                    batch = video_ids[i:i+50]
                    ids_string = ",".join(batch)
                    
                    url = f"{self.base_url}/videos?part=snippet,statistics,contentDetails&id={ids_string}&key={self.api_key}"
                    
                    await page.goto(url)
                    data = json.loads(await page.evaluate("() => document.body.innerText"))
                    
                    if "error" in data:
                        print(f"❌ API Error: {data['error']['message']}")
                        return None
                    
                    all_videos.extend(data.get("items", []))
                    progress = min(i + 50, len(video_ids))
                    print(f"  ✓ Fetched {progress}/{len(video_ids)} videos")
                
                print(f"✅ Fetched statistics for {len(all_videos)} videos")
                return all_videos
                
            finally:
                await context.close()
                await browser.close()
    
    def create_csv(self, videos: list[dict]):
        """Create a properly formatted CSV file from video data."""
        print(f"📝 Creating CSV file...")
        
        rows = [
            ["video_id", "title", "video_description", "video_length", "video_published_datetime", "video_likes", "video_views", "number_comments"]
        ]
        
        for video in videos:
            snippet = video.get("snippet", {})
            stats = video.get("statistics", {})
            content_details = video.get("contentDetails", {})
            
            row = [
                video.get("id", ""),
                snippet.get("title", ""),
                snippet.get("description", "").replace("\n", " ").replace("\r", " "),  # Remove newlines
                content_details.get("duration", ""),
                snippet.get("publishedAt", ""),
                stats.get("likeCount", "0"),
                stats.get("viewCount", "0"),
                stats.get("commentCount", "0"),
            ]
            rows.append(row)
        
        # Write CSV file
        output_path = Path(self.output_filename)
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)
        
        print(f"✅ CSV created: {output_path}")
        print(f"   Total rows: {len(rows) - 1} videos")
        
        return output_path
    
    async def run(self):
        """Execute the full scraping workflow."""
        print("\\n" + "="*60)
        print("🎬 YouTube Playlist to CSV Converter")
        print("="*60 + "\\n")
        
        # Step 1: Fetch playlist items
        playlist_items = await self.fetch_playlist_items()
        if not playlist_items:
            return
        
        # Step 2: Extract video IDs
        video_ids = [item["contentDetails"]["videoId"] for item in playlist_items]
        
        # Step 3: Fetch video statistics
        videos = await self.fetch_video_stats(video_ids)
        if not videos:
            return
        
        # Step 4: Create CSV
        output_file = self.create_csv(videos)
        
        print("\\n" + "="*60)
        print(f"✨ Success! CSV saved to: {output_file}")
        print("="*60 + "\\n")


def main(playlist_id: str = typer.Argument(..., help="YouTube playlist ID to scrape")):
    """Main entry point for the YouTube Playlist Scraper CLI."""
    # Load environment variables
    load_dotenv()
    
    # Configuration
    API_KEY = os.getenv("YOUTUBE_API_KEY")  # Your API key from .env file
    
    if not API_KEY:
        raise ValueError("YOUTUBE_API_KEY not found in environment variables")
    
    # Create data directory if it doesn't exist
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Generate timestamp for filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_filename = data_dir / f"youtube_playlist_{playlist_id}_{timestamp}.csv"
    
    # Create scraper instance
    scraper = YouTubePlaylistScraper(
        playlist_id=playlist_id,
        api_key=API_KEY,
        output_filename=str(output_filename)
    )
    
    # Run the scraper
    asyncio.run(scraper.run())


if __name__ == "__main__":
    typer.run(main)