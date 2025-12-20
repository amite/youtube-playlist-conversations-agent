### Plan Summary

Location: artifacts/wip/plans/phase-0-2-semantic-cleaning-plan.md

Key Findings from Exploration

The plan is built on detailed analysis of your codebase: Current State:
410 videos ingested with basic Phase 0.1 cleaning
cleaned_title and cleaned_description columns exist but are empty
Significant data noise identified:
89.8% have URLs
58.8% have timestamps
30.2% have social CTAs

Titles contain excessive caps, emojis, clickbait patterns

#### Implementation Approach:

12+ semantic cleaning functions in utils/cleaning.py targeting specific noise patterns
Script to apply cleaning to all 410 existing videos with dry-run validation
Validation tool for side-by-side comparison of raw vs cleaned data
Integration updates to ensure future ingestion uses cleaned columns

### Why This Approach

Regex-based (no heavy dependencies): Lightweight, transparent, easy to debug
Reversible: Raw columns preserved for A/B testing and debugging
Iterative: Dry-run mode lets you preview changes before applying
Validated: Built-in sampling and metrics to catch over-cleaning
What's Ready to Review
The plan includes:
7 implementation steps with detailed function specifications
Complete code templates for new scripts
Success criteria and validation strategy
Known challenges with solutions
Realistic 6-8 hour timeline broken down by step
Please review the plan and let me know if you'd like any adjustments before we proceed with implementation!