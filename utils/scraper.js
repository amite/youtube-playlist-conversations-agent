(async () => {
    const API_KEY = '***';
    const PLAYLIST_ID = '***';

    console.log('Starting CSV generation...');

    try {
        // STEP 1: Fetch all playlist items
        console.log('Fetching playlist items...');
        let allItems = [];
        let pageToken = null;
        let pageCount = 0;

        while (true) {
            let url = 'https://www.googleapis.com/youtube/v3/playlistItems?part=snippet,contentDetails&playlistId=' + PLAYLIST_ID + '&maxResults=50&key=' + API_KEY;
            if (pageToken) url += '&pageToken=' + pageToken;

            const response = await fetch(url);
            const data = await response.json();

            if (data.error) {
                console.error('API Error:', data.error.message);
                return;
            }

            allItems = allItems.concat(data.items || []);
            pageCount++;
            console.log('Fetched page ' + pageCount + ', total items: ' + allItems.length);

            if (!data.nextPageToken) break;
            pageToken = data.nextPageToken;
        }

        console.log('Total playlist items: ' + allItems.length);

        // STEP 2: Extract video IDs and fetch video statistics
        console.log('Fetching video statistics...');
        const videoIds = allItems.map(item => item.contentDetails.videoId);
        let allVideos = [];

        for (let i = 0; i < videoIds.length; i += 50) {
            const batch = videoIds.slice(i, i + 50);
            const idsString = batch.join(',');
            const url = 'https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics,contentDetails&id=' + idsString + '&key=' + API_KEY;

            const response = await fetch(url);
            const data = await response.json();

            if (data.error) {
                console.error('API Error:', data.error.message);
                return;
            }

            allVideos = allVideos.concat(data.items || []);
            console.log('Fetched ' + allVideos.length + ' videos...');
        }

        console.log('Total videos with stats: ' + allVideos.length);

        // STEP 3: Create CSV with proper formatting
        console.log('Creating CSV...');

        const QUOTE = String.fromCharCode(34);
        const NEWLINE = String.fromCharCode(10);
        const COMMA = String.fromCharCode(44);

        // CSV Header
        let csv = 'title' + COMMA + 'video_description' + COMMA + 'video_length' + COMMA + 'video_published_datetime' + COMMA + 'video_likes' + COMMA + 'video_views' + COMMA + 'number_comments' + NEWLINE;

        // CSV Rows - with proper RFC 4180 escaping
        for (let i = 0; i < allVideos.length; i++) {
            const v = allVideos[i];

            // Escape quotes by doubling them, remove newlines from descriptions
            const title = (v.snippet.title || '').split(QUOTE).join(QUOTE + QUOTE);
            const description = (v.snippet.description || '').split(QUOTE).join(QUOTE + QUOTE).split(NEWLINE).join(' ');
            const length = v.contentDetails.duration || '';
            const publishedAt = v.snippet.publishedAt || '';
            const likes = v.statistics.likeCount || '0';
            const views = v.statistics.viewCount || '0';
            const comments = v.statistics.commentCount || '0';

            // All fields quoted for RFC 4180 compliance
            csv += QUOTE + title + QUOTE + COMMA + QUOTE + description + QUOTE + COMMA + length + COMMA + publishedAt + COMMA + likes + COMMA + views + COMMA + comments + NEWLINE;
        }

        console.log('CSV created - size: ' + csv.length + ' bytes');

        // STEP 4: Download the file
        console.log('Generating download...');

        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);

        link.setAttribute('href', url);
        link.setAttribute('download', 'youtube_playlist.csv');
        link.style.visibility = 'hidden';

        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        console.log('✓ Download complete! File: youtube_playlist.csv');
        console.log('✓ Total rows: ' + allVideos.length);

    } catch (error) {
        console.error('Error:', error.message);
    }
})();