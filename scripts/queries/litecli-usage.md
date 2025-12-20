Basic Usage
Simply run litecli with your database file:

```bash
litecli data/videos.db
```

This opens an interactive terminal where you can write SQL queries with syntax highlighting and auto-completion.
Viewing Your Query Results in Color
Once in the litecli interactive shell, you can run your queries:

```bash
.read scripts/queries/overview.sql
```
Or run individual queries directly:

SELECT * FROM videos LIMIT 10;
The output will display in color-coded tables with:
Syntax highlighting for your SQL
Pretty-printed results in table format
Auto-completion as you type (tab key)
Useful Options
Run a query and exit immediately:

litecli data/videos.db -e "SELECT * FROM videos LIMIT 5;"
Display output in specific formats: Inside litecli, use these commands:
.mode column - Colored table format (default)
.mode csv - CSV output
.mode json - JSON format
.mode vertical - Vertical layout
Auto-switch to vertical output if results are wide:

litecli --auto-vertical-output data/videos.db
Log all queries to a file:

litecli data/videos.db --logfile query_log.txt
Quick Example with Your Queries

litecli data/videos.db
Then at the prompt, you can pipe your SQL scripts:

.read scripts/queries/overview.sql
The colored output will make it much easier to read your query results! All your column names, types, and values will be displayed in a nicely formatted, color-coded table. Sources:
LiteCLI GitHub Repository
LiteCLI Official Website
LiteCLI Usage Documentation