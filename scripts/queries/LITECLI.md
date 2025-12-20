# LiteCLI Query Scripts

This folder contains **litecli-compatible** SQL query scripts that work with colored output and syntax highlighting in the litecli terminal UI.

## Quick Start

```bash
# Enter interactive litecli shell with colored output
uv run litecli data/videos.db

# Inside litecli, load any query file with .read:
.read scripts/queries/overview-litecli.sql
.read scripts/queries/channels-litecli.sql
.read scripts/queries/evaluation_summary-litecli.sql
# etc. - just type the query name and press Enter!

# You get colored output, pretty tables, and full interactivity!
```

## Available Scripts

### Core Queries

1. **overview-litecli.sql** - Database overview & key metrics
   - Total videos, channels, indexing progress
   - Content metrics (duration, views, likes)
   - Engagement rates & table record counts

2. **channels-litecli.sql** - Channel analysis & performance
   - Top channels by video count
   - Channel distribution tiers
   - Most active channels
   - Highest engagement channels

3. **content_stats-litecli.sql** - Content distribution & engagement
   - Video length distribution
   - Popularity tiers
   - Engagement metrics
   - Most/least viewed videos
   - Publication date trends

4. **embedding_progress-litecli.sql** - Embedding tracking & API costs
   - Embedding generation status
   - Embeddings log summary
   - API cost analysis
   - Timeline of embedding generation
   - Projections for remaining videos

5. **evaluation_summary-litecli.sql** - Search quality metrics
   - Evaluation summary & counts
   - Relevance score distribution
   - Best result position analysis
   - Evaluation by query type
   - Recent evaluations & timeline

6. **data_quality-litecli.sql** - Data integrity checks
   - Data completeness analysis
   - NULL field summary
   - Potential duplicates
   - Outlier detection (long videos, extreme views, short videos)
   - Data entry issues

7. **trending_analysis-litecli.sql** - Temporal patterns & trends
   - Most recent videos
   - Videos from last 30/90 days/1 year
   - Publication trends by year/month
   - Most viewed videos in last year
   - Oldest videos in database
   - View growth patterns

8. **search_testing-litecli.sql** - Test query suite status
   - Test query suite status
   - Queries by type
   - Evaluation coverage
   - All test queries with status
   - Queries without evaluations
   - Highest/lowest rated queries

### Extended Queries

9. **cost_analysis-litecli.sql** - API cost tracking & projections
   - Embedding cost summary
   - Historical costs by type
   - Cost per video analysis
   - Projections for remaining videos
   - Total project cost estimates
   - Cost by channel & daily/weekly trends

10. **comparison_queries-litecli.sql** - Before/after algorithm comparisons
    - Overall evaluation metrics
    - Relevance score distribution
    - Evaluation metrics by time period
    - Daily evaluation trends
    - Performance by query type
    - Queries showing improvement/regression

11. **export_reports-litecli.sql** - Statistical reports
    - Channel leaderboard
    - Content distribution report
    - Search quality scorecard
    - Top 20 videos by views
    - Data quality summary
    - Complete video catalog
    - Embedding cost report
    - Test query results matrix

## Usage

### Interactive Mode (Recommended - Full Colors & Highlighting)

```bash
# Start litecli
uv run litecli data/videos.db

# Inside litecli, load any query file with .read:
.read scripts/queries/overview-litecli.sql
.read scripts/queries/channels-litecli.sql
.read scripts/queries/evaluation_summary-litecli.sql

# Or type queries directly and get:
# 1. Auto-completion (tab key)
# 2. Colored syntax highlighting
# 3. Pretty formatted tables
# 4. Interactive result browsing
```

### Batch Mode (Pipe through litecli)

```bash
# Run a query file through litecli (shows colors)
uv run litecli data/videos.db < scripts/queries/overview-litecli.sql

# Save output to a file
uv run litecli data/videos.db < scripts/queries/overview-litecli.sql > report.txt

# View first 100 lines
uv run litecli data/videos.db < scripts/queries/overview-litecli.sql | head -100
```

## Differences from Original Scripts

The `-litecli.sql` versions remove SQLite dot commands (`.headers on`, `.mode column`, `.mode csv`, etc.) because:

- **LiteCLI handles formatting automatically** - It doesn't interpret dot commands the same way
- **Colors & pretty printing are built-in** - LiteCLI applies formatting automatically
- **Cleaner output** - No need to manage modes manually

### Original vs LiteCLI

| Original | LiteCLI |
|----------|---------|
| `sqlite3 -header -column data/videos.db < overview.sql` | `uv run litecli data/videos.db < overview-litecli.sql` |
| Plain white text | Colored syntax highlighting |
| Manual formatting | Automatic table formatting |
| `.mode csv` / `.mode column` / `.mode markdown` support | Single format (litecli optimized) |

## Color Features

LiteCLI provides:
- ✅ **Syntax highlighted SQL** - Keywords, strings, numbers in different colors
- ✅ **Colored table output** - Headers and data distinguished visually
- ✅ **Auto-completion** - Table names, columns, keywords with tab completion
- ✅ **Better readability** - Structured output in monospace terminal UI
- ✅ **Scrollable results** - Navigate through large result sets easily

## Pro Tips

### 1. Use LiteCLI Interactively for Best Experience
```bash
uv run litecli data/videos.db

# Inside litecli, load queries with .read:
.read scripts/queries/overview-litecli.sql

# Then press Enter to execute!
```
You get full interactivity with colors - no copy-paste needed!

### 2. Pipe for Quick Analysis
```bash
# Get quick stats without opening interactive shell
uv run litecli data/videos.db < scripts/queries/overview-litecli.sql
```

### 3. Combine with Standard Tools
```bash
# Filter results with grep (colors work with most terminals)
uv run litecli data/videos.db < scripts/queries/channels-litecli.sql | grep freeCodeCamp

# Get specific number of rows
uv run litecli data/videos.db < scripts/queries/content_stats-litecli.sql | head -30

# Save to file for documentation
uv run litecli data/videos.db < scripts/queries/evaluation_summary-litecli.sql > docs/evaluation-report.txt
```

### 4. Compare Multiple Outputs
```bash
# Run before change
uv run litecli data/videos.db < scripts/queries/overview-litecli.sql > before.txt

# Make your changes...

# Run after change
uv run litecli data/videos.db < scripts/queries/overview-litecli.sql > after.txt

# Compare
diff before.txt after.txt
```

## When to Use Standard sqlite3 vs LiteCLI

| Task | Tool | Why |
|------|------|-----|
| Quick colored overview | LiteCLI interactive | Best UX, colors, completion |
| Scripting/automation | `sqlite3` | Better for piping, no interactive features |
| Export to CSV | `sqlite3 -header` | More reliable CSV handling |
| Generate reports | `sqlite3` | Easy to save formatted output |
| Daily monitoring | LiteCLI | Visual feedback, easy to re-run |
| Code review analysis | LiteCLI | Colors help spot patterns |

## See Also

- [Original SQL queries](README.md) - Non-litecli versions for scripting
- [QUICK_START.sh](QUICK_START.sh) - Quick reference guide
- LiteCLI Docs: https://litecli.com/

## FAQ

**Q: Why do I get "near '.': syntax error"?**
A: You're using the original `.sql` files with litecli. Use the `-litecli.sql` versions instead!

**Q: Can I use these with regular sqlite3?**
A: Yes! They're pure SQL - litecli is just the viewer. But use the original files if you need `.mode csv` support.

**Q: How do I exit litecli?**
A: Type `exit` or `.exit` or press Ctrl+D

**Q: Does litecli slow down large queries?**
A: No, it just displays the results. Query performance is the same.

**Q: Can I use these in a script/cron job?**
A: Yes! Pipe them like: `uv run litecli data/videos.db < query.sql >> logfile.txt`
