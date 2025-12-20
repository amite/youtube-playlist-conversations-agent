import asyncio
import csv
from pathlib import Path
from playwright.async_api import async_playwright
import json
from datetime import datetime
import os
from dotenv import load_dotenv
import typer
import sqlite3


class YouTubePlaylistScraper:
    def __init__(self, playlist_id: str, api_key: str, output_filename: str | None = None, db_path: str | None = None):
        """
        Initialize the YouTube playlist scraper.

        Args:
            playlist_id: YouTube playlist ID (from URL: list=PLAYLIST_ID)
            api_key: YouTube Data API key
            output_filename: Optional custom output filename
            db_path: Optional path to SQLite database for incremental scraping
        """
        self.playlist_id = playlist_id
        self.api_key = api_key
        self.output_filename = output_filename or f"playlist_{playlist_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.db_path = db_path
        self.existing_video_ids = self._load_existing_video_ids()

    def _load_existing_video_ids(self) -> set[str]:
        """Load existing video IDs from database to skip re-fetching."""
        if not self.db_path or not Path(self.db_path).exists():
            return set()

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT video_id FROM videos")
            existing_ids = {row[0] for row in cursor.fetchall()}
            conn.close()
            print(f"📂 Loaded {len(existing_ids)} existing video IDs from database")
            return existing_ids
        except Exception as e:
            print(f"⚠️  Could not load existing IDs: {e}")
            return set()

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

                    items = data.get("items", [])

                    # Filter out existing videos if database provided
                    if self.existing_video_ids:
                        new_items = [
                            item for item in items
                            if item["contentDetails"]["videoId"] not in self.existing_video_ids
                        ]
                        skipped = len(items) - len(new_items)
                        all_items.extend(new_items)
                        print(f"  ✓ Page {page_count + 1}: {len(new_items)} new, {skipped} skipped")
                    else:
                        all_items.extend(items)
                        print(f"  ✓ Page {page_count + 1}: {len(all_items)} items total")

                    page_count += 1
                    
                    if "nextPageToken" not in data:
                        break
                    
                    page_token = data["nextPageToken"]

                if self.existing_video_ids:
                    print(f"✅ Fetched {len(all_items)} NEW playlist items ({len(self.existing_video_ids)} existing skipped)")
                else:
                    print(f"✅ Fetched {len(all_items)} playlist items")

                # Early exit if no new videos
                if len(all_items) == 0 and self.existing_video_ids:
                    print("ℹ️  No new videos found in playlist")
                    return []

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
    
    def _find_previous_csv(self) -> Path | None:
        """Find the most recent previous CSV file (excluding current output file)."""
        data_dir = Path(self.output_filename).parent
        playlist_id = self.playlist_id

        # Find all CSV files for this playlist, sorted by modification time
        csv_files = sorted(
            data_dir.glob(f"youtube_playlist_{playlist_id}_*.csv"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        # Return second most recent (first is the one we're about to write)
        if len(csv_files) > 1:
            return csv_files[1]
        return None

    def _append_previous_csv_rows(self, output_path: Path) -> int:
        """Append rows from previous CSV to the new CSV (excluding header)."""
        previous_csv = self._find_previous_csv()
        if not previous_csv:
            return 0

        try:
            with open(output_path, "a", newline="", encoding="utf-8") as output_file:
                with open(previous_csv, "r", newline="", encoding="utf-8") as prev_file:
                    reader = csv.reader(prev_file)
                    writer = csv.writer(output_file)

                    # Skip header row of previous CSV
                    next(reader, None)

                    # Append all data rows
                    rows_appended = 0
                    for row in reader:
                        writer.writerow(row)
                        rows_appended += 1

            return rows_appended
        except Exception as e:
            print(f"⚠️  Could not append previous CSV: {e}")
            return 0

    def _log_scraper_run(
        self,
        new_count: int,
        skipped_count: int,
        total_csv_rows: int,
        csv_path: str,
        start_time: datetime,
        status: str = "success",
        error: str = None,
    ):
        """Log scraper run to database for historical tracking."""
        if not self.db_path:
            return  # No database, skip logging

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO scraper_runs (
                    playlist_id, run_started_at, run_completed_at,
                    new_videos_count, existing_videos_skipped, total_videos_in_csv,
                    csv_path, status, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.playlist_id,
                    start_time.isoformat(),
                    datetime.now().isoformat(),
                    new_count,
                    skipped_count,
                    total_csv_rows,
                    str(csv_path),
                    status,
                    error,
                ),
            )
            conn.commit()
            run_id = cursor.lastrowid
            conn.close()
            print(f"📊 Run logged to database (ID: {run_id})")
        except Exception as e:
            print(f"⚠️  Could not log scraper run: {e}")

    def create_csv(self, videos: list[dict], playlist_items: list[dict]):
        """Create a properly formatted CSV file from video data."""
        print(f"📝 Creating CSV file...")

        rows = [
            ["video_id", "channel_name", "title", "video_description", "video_length", "video_published_datetime", "video_likes", "video_views", "number_comments"]
        ]

        # Create a mapping of video_id to channel name
        video_channel_map = {}
        for item in playlist_items:
            video_id = item["contentDetails"]["videoId"]
            channel_name = item["snippet"].get("videoOwnerChannelTitle", item["snippet"]["channelTitle"])
            video_channel_map[video_id] = channel_name

        for video in videos:
            snippet = video.get("snippet", {})
            stats = video.get("statistics", {})
            content_details = video.get("contentDetails", {})

            row = [
                video.get("id", ""),
                video_channel_map.get(video.get("id", ""), ""),  # Channel name
                snippet.get("title", ""),
                snippet.get("description", "").replace("\n", " ").replace("\r", " "),  # Remove newlines
                content_details.get("duration", ""),
                snippet.get("publishedAt", ""),
                stats.get("likeCount", "0"),
                stats.get("viewCount", "0"),
                stats.get("commentCount", "0"),
            ]
            rows.append(row)

        # Write CSV file with new videos
        output_path = Path(self.output_filename)
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

        # Append old videos from previous CSV (if incremental scraping)
        new_video_count = len(rows) - 1
        skipped_count = 0
        if self.existing_video_ids:
            appended_count = self._append_previous_csv_rows(output_path)
            total_count = new_video_count + appended_count
            skipped_count = len(self.existing_video_ids)
            print(f"✅ CSV created: {output_path}")
            print(f"   New videos: {new_video_count}")
            print(f"   Previous videos: {appended_count}")
            print(f"   Total rows: {total_count} videos")
        else:
            print(f"✅ CSV created: {output_path}")
            print(f"   Total rows: {new_video_count} videos")

        return output_path, new_video_count, skipped_count
    
    async def run(self):
        """Execute the full scraping workflow."""
        start_time = datetime.now()
        print("\\n" + "="*60)
        print("🎬 YouTube Playlist to CSV Converter")
        print("="*60 + "\\n")

        try:
            # Step 1: Fetch playlist items
            playlist_items = await self.fetch_playlist_items()
            if not playlist_items:
                print("\nℹ️  No new videos to process. Database is up to date!")
                # Log no-op run to database
                self._log_scraper_run(
                    new_count=0,
                    skipped_count=len(self.existing_video_ids),
                    total_csv_rows=0,
                    csv_path="",
                    start_time=start_time,
                    status="skipped",
                )
                return

            # Step 2: Extract video IDs
            video_ids = [item["contentDetails"]["videoId"] for item in playlist_items]

            # Step 3: Fetch video statistics
            videos = await self.fetch_video_stats(video_ids)
            if not videos:
                return

            # Step 4: Create CSV
            output_file, new_count, skipped_count = self.create_csv(videos, playlist_items)

            # Step 5: Log run to database
            total_csv_rows = new_count + (len(self.existing_video_ids) if self.existing_video_ids else new_count)
            self._log_scraper_run(
                new_count=new_count,
                skipped_count=skipped_count,
                total_csv_rows=total_csv_rows,
                csv_path=output_file,
                start_time=start_time,
            )

            print("\\n" + "="*60)
            print(f"✨ Success! CSV saved to: {output_file}")
            print("="*60 + "\\n")
        except Exception as e:
            # Log error to database
            self._log_scraper_run(
                new_count=0,
                skipped_count=0,
                total_csv_rows=0,
                csv_path="",
                start_time=start_time,
                status="failed",
                error=str(e),
            )
            raise


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

    # Database path for incremental scraping
    db_path = data_dir / "videos.db"

    # Create scraper instance
    scraper = YouTubePlaylistScraper(
        playlist_id=playlist_id,
        api_key=API_KEY,
        output_filename=str(output_filename),
        db_path=str(db_path) if db_path.exists() else None
    )
    
    # Run the scraper
    asyncio.run(scraper.run())


if __name__ == "__main__":
    typer.run(main)