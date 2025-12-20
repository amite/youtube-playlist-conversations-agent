# Session Summaries

Compact markdown summaries of long coding sessions, automatically saved for context continuity across sessions.

## Naming Convention

Files are named with the pattern: `YYYYMMDD-brief-title.md`

- **YYYYMMDD**: Date the summary was created (ISO 8601 format)
- **brief-title**: Short, kebab-case description of the session's focus

## Example Files

- `20251220-data-cleaning-plan.md` - Planning session for Phase 1 data cleaning pipeline

## How to Use

### In a New Session

Start your new chat with:

```markdown
# Prior Context

[paste contents of the summary file OR reference the file path]
```

Then say: "Continue from where I left off" or "Let's implement Phase 0.1"

### For the Session Refiner Skill

When you want to create a summary, ask:

```
Use Session Refiner to create a summary
```

Claude will:
1. Automatically generate a summary
2. Save it here with a timestamped filename
3. Display the file path for your reference

## What's Included

Each summary contains:
- **Current Status**: Active tasks and TODOs
- **Key Technical Decisions**: Architectural choices made
- **Resolved Issues**: Bugs fixed, problems solved
- **Key Findings**: Important discoveries and notes
- **Code References**: Essential code snippets
- **Next Steps**: What to do in the next session

## Storage

- Location: `.claude/session-summaries/`
- Size: Typically 2-5 KB per summary (2,000-5,000 tokens)
- Retention: Keep indefinitely for project continuity
