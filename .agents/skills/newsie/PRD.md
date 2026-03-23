# Newsie PRD

## Overview

Newsie is a personalized AI assistant that fetches today's tech news and delivers a briefing. It solves the problem of staying up-to-date with current events in the tech field by searching the web, fetching articles, and generating a formatted markdown briefing. Newsie supports explicit preference configuration via interactive setup, persists user preferences and feedback across sessions in JSON, and ranks articles by recency, relevance, and source credibility.

---

## Task 1: Interactive Setup Command

- Implemented: true
- Test Passed: true
- Goal: Implement `newsie setup` command that interactively configures user preferences
- Inputs: User responses to interactive prompts
- Outputs: `newsie.config.json` file with preferences and feedback objects
- Specification 1: Prompt for preferred companies (e.g., Apple, Google, Microsoft)
- Specification 2: Prompt for preferred topics (e.g., AI, cybersecurity, startups)
- Specification 3: Prompt for number of articles (default: 5)
- Specification 4: Store config in JSON with separate `preferences` and `feedback` objects
- Specification 5: Create `outputs/` folder if it doesn't exist
- Test Case: Run `newsie setup`, provide test values, verify config file structure

---

## Task 2: Briefing Generation Command

- Implemented: true
- Test Passed: true
- Goal: Implement `newsie briefing` command that fetches and generates a news briefing
- Inputs: CLI arguments, user preferences from config file
- Outputs: Markdown briefing file in `outputs/` folder
- Specification 1: Fetch news using search engines and web scraping
- Specification 2: Default to international news (not just USA)
- Specification 3: Fetch default 5 articles (or user-configured count)
- Specification 4: Include article metadata: publish date, author, source domain
- Specification 5: Include headline and summary for each article
- Specification 6: Include source links for each article
- Specification 7: Rank articles by recency (newest first), then relevance to preferred topics, then source credibility
- Specification 8: Output as markdown file with timestamp in filename
- Test Case: Run `newsie briefing`, verify markdown output contains 5 articles with required metadata

---

## Task 3: Markdown Output Formatting

- Implemented: true
- Test Passed: true
- Goal: Format briefing output as structured markdown with visual styling
- Inputs: Article data (headline, summary, metadata, source link)
- Outputs: Formatted markdown file
- Specification 1: Use bold text for headlines
- Specification 2: Use italics for source names
- Specification 3: Use horizontal rules between articles
- Specification 4: Use emoji indicators for topic categories
- Specification 5: Organize into sections: headlines, summaries, source links
- Test Case: Verify markdown renders correctly with all formatting elements

---

## Task 4: Edge Case Handling

- Implemented: true
- Test Passed: true
- Goal: Handle edge cases gracefully
- Inputs: Search results that may be empty, conflicting, or duplicate
- Outputs: User-friendly messages or filtered results
- Specification 1: Display message when no news found for preferred topics
- Specification 2: Detect and flag conflicting reports (e.g., note contradictory claims)
- Specification 3: Deduplicate stories across sources (keep only unique stories)
- Test Case: Simulate empty search results, verify appropriate message is shown

---

## Task 5: Feedback System

- Implemented: true
- Test Passed: true
- Goal: Allow users to provide feedback on briefing quality and topic coverage
- Inputs: User feedback via CLI (rating, topic coverage requests)
- Outputs: Updated feedback stored in `newsie.config.json`
- Specification 1: Accept feedback on briefing quality
- Specification 2: Accept requests for more/less coverage of certain topics
- Specification 3: Persist feedback across sessions in the `feedback` object
- Specification 4: Use feedback to adjust future briefings automatically
- Test Case: Submit feedback, run new briefing, verify adjustments are applied

---

## Task 6: CLI Interface

- Implemented: true
- Test Passed: false
- Goal: Implement command-line interface with subcommands
- Inputs: Command-line arguments
- Outputs: Executed commands with appropriate responses
- Specification 1: Support `newsie setup` subcommand
- Specification 2: Support `newsie briefing` subcommand
- Specification 3: Support `--topics` flag to override preferred topics
- Specification 4: Support `--count` flag to override article count
- Specification 5: Written in Python
- Test Case: Run all CLI commands, verify correct behavior

---

## Task 7: News Fetching Module

- Implemented: true
- Test Passed: false
- Goal: Implement module to fetch news from search engines and via web scraping
- Inputs: Preferred topics, companies, regions
- Outputs: List of articles with metadata
- Specification 1: Use search engines (e.g., Tavily, SerpAPI) to find news
- Specification 2: Use web scraping to extract article content
- Specification 3: Extract metadata: publish date, author, source domain
- Specification 4: Extract headline and summary
- Specification 5: Handle API rate limiting gracefully
- Test Case: Mock API responses, verify article extraction works correctly

---
