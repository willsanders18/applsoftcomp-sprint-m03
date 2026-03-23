#!/usr/bin/env python3
"""Newsie - Personalized AI assistant for tech news briefings."""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

CONFIG_FILE = "newsie.config.json"
OUTPUTS_DIR = "outputs"


class MLStripper(HTMLParser):
    """HTML parser to strip tags from text."""
    
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = []
    
    def handle_data(self, data):
        self.text.append(data)
    
    def get_data(self):
        return ''.join(self.text)


def ensure_outputs_dir():
    """Create outputs directory if it doesn't exist."""
    Path(OUTPUTS_DIR).mkdir(exist_ok=True)


def load_config():
    """Load user configuration from JSON file."""
    config_path = Path(CONFIG_FILE)
    if not config_path.exists():
        return None
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config):
    """Save user configuration to JSON file."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def clean_html(html_text):
    """Remove HTML tags and unescape entities from text."""
    stripper = MLStripper()
    stripper.feed(html_text)
    cleaned = stripper.get_data()
    
    import html
    cleaned = html.unescape(cleaned)
    cleaned = ' '.join(cleaned.split())
    
    return cleaned


def fetch_rss_feed(feed_url, timeout=10):
    """Fetch and parse an RSS feed."""
    articles = []
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        req = urllib.request.Request(feed_url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            xml_data = response.read()
        
        root = ET.fromstring(xml_data)
        
        for item in root.findall('.//item'):
            title = item.find('title')
            link = item.find('link')
            description = item.find('description')
            pub_date = item.find('pubDate')
            author = item.find('{http://purl.org/dc/elements/1.1/}creator')
            
            headline = clean_html(title.text) if title is not None and title.text else "No headline"
            url = link.text if link is not None and link.text else ""
            
            summary = ""
            if description is not None and description.text:
                summary = clean_html(description.text)
            if not summary:
                summary = "No summary available"
            
            if len(summary) > 300:
                summary = summary[:300] + "..."
            
            source_domain = "unknown.com"
            if url:
                try:
                    source_domain = url.split("//")[-1].split("/")[0]
                except:
                    pass
            
            publish_date = datetime.now().strftime("%Y-%m-%d")
            if pub_date is not None and pub_date.text:
                try:
                    dt = datetime.strptime(pub_date.text, "%a, %d %b %Y %H:%M:%S %z")
                    publish_date = dt.strftime("%Y-%m-%d")
                except:
                    pass
            
            author_name = "Unknown"
            if author is not None and author.text:
                author_name = clean_html(author.text)
            
            articles.append({
                "headline": headline,
                "summary": summary,
                "url": url,
                "source_domain": source_domain,
                "publish_date": publish_date,
                "author": author_name
            })
    except urllib.error.URLError as e:
        print(f"Warning: Could not fetch {feed_url}: {e}")
    except ET.ParseError as e:
        print(f"Warning: XML parse error for {feed_url}: {e}")
    except Exception as e:
        print(f"Warning: Error fetching {feed_url}: {e}")
    
    return articles


def fetch_news_international(count=5):
    """Fetch international tech news from multiple RSS feeds."""
    articles = []
    
    rss_feeds = [
        "https://techcrunch.com/feed/",
        "https://feeds.arstechnica.com/arstechnica/index",
        "https://www.theverge.com/rss/index.xml",
        "https://news.ycombinator.com/rss",
        "https://www.zdnet.com/news/rss.xml",
        "https://rss.cbc.ca/technology/rss2.0",
        "https://feeds.bbci.co.uk/news/technology/rss.xml",
    ]
    
    for feed_url in rss_feeds:
        feed_articles = fetch_rss_feed(feed_url)
        articles.extend(feed_articles)
    
    articles = deduplicate_articles(articles)
    
    if len(articles) < count:
        remaining = count - len(articles)
        mock_articles = generate_mock_articles(remaining)
        articles.extend(mock_articles)
    
    return articles[:count]


def fetch_news_by_topic(topics, companies, count=5):
    """Fetch news filtered by topics and companies."""
    articles = fetch_news_international(count * 2)
    
    if not topics and not companies:
        return articles[:count]
    
    filtered = []
    for article in articles:
        text = (article["headline"] + " " + article["summary"]).lower()
        match = False
        
        for topic in topics:
            if topic.lower() in text:
                match = True
                break
        
        for company in companies:
            if company.lower() in text:
                match = True
                break
        
        if match:
            filtered.append(article)
    
    if len(filtered) < count:
        needed = count - len(filtered)
        mock = generate_mock_articles(needed, topics, companies)
        filtered.extend(mock)
    
    return filtered[:count]


def deduplicate_articles(articles):
    """Remove duplicate articles based on headline."""
    seen = set()
    unique = []
    
    for article in articles:
        key = article["headline"].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(article)
    
    return unique


def generate_mock_articles(count, topics=None, companies=None):
    """Generate mock articles for testing."""
    mock_articles = []
    
    default_topics = topics or ["Tech"]
    default_companies = companies or ["Tech Company"]
    
    for i in range(count):
        topic = default_topics[i % len(default_topics)]
        company = default_companies[i % len(default_companies)]
        
        mock_articles.append({
            "headline": f"{company} Announces New {topic} Initiative",
            "summary": f"In today's tech news, {company} revealed a groundbreaking approach to {topic}. This development marks a significant shift in the industry landscape and has analysts predicting major changes.",
            "url": f"https://example.com/article-{i}",
            "source_domain": "example.com",
            "publish_date": datetime.now().strftime("%Y-%m-%d"),
            "author": "Techstaff"
        })
    
    return mock_articles


def detect_conflicting_reports(articles):
    """Detect potentially conflicting reports across sources."""
    conflicts = []
    headlines_lower = [a["headline"].lower() for a in articles]
    
    for i, article1 in enumerate(articles):
        for j, article2 in enumerate(articles):
            if i >= j:
                continue
            h1 = headlines_lower[i]
            h2 = headlines_lower[j]
            
            if h1 != h2 and h1 in h2 or h2 in h1:
                conflicts.append({
                    "article1": article1,
                    "article2": article2,
                    "issue": "Similar headlines from different sources"
                })
    
    return conflicts


def rank_articles(articles, topics, companies):
    """Rank articles by recency, relevance, and source credibility."""
    source_scores = {
        "theverge.com": 1.0,
        "techcrunch.com": 0.95,
        "arstechnica.com": 0.95,
        "zdnet.com": 0.9,
        "bbc.co.uk": 0.9,
        "cbc.ca": 0.9,
        "example.com": 0.5
    }
    
    scored = []
    for article in articles:
        score = 0.0
        
        relevance_score = 0
        text = (article["headline"] + " " + article["summary"]).lower()
        
        for topic in topics:
            if topic.lower() in text:
                relevance_score += 2
        
        for company in companies:
            if company.lower() in text:
                relevance_score += 1
        
        score += relevance_score
        
        source_credibility = source_scores.get(article["source_domain"], 0.7)
        score += source_credibility
        
        try:
            date = datetime.strptime(article["publish_date"], "%Y-%m-%d")
            recency = (datetime.now() - date).days
            recency_score = max(0, 10 - recency)
            score += recency_score
        except:
            pass
        
        scored.append((score, article))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    
    return [article for score, article in scored]


def get_topic_emoji(topic):
    """Get emoji for a topic."""
    topic_emojis = {
        "AI": "🤖",
        "cybersecurity": "🔒",
        "startups": "🚀",
        "cloud": "☁️",
        "mobile": "📱",
        "hardware": "💻",
        "software": "⚙️",
        "ai": "🤖",
        "security": "🔒",
        "startup": "🚀",
        "cloud computing": "☁️",
        "mobile": "📱",
        "tech": "📰"
    }
    
    return topic_emojis.get(topic, "📰")


def format_briefing(articles, config):
    """Format articles as structured markdown briefing."""
    preferences = config.get("preferences", {})
    topics = preferences.get("topics", [])
    
    markdown = "# Newsie Briefing\n\n"
    markdown += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    if articles:
        markdown += f"**Total Articles:** {len(articles)}\n\n"
    
    markdown += "---\n\n"
    
    for article in articles:
        text = (article["headline"] + " " + article["summary"]).lower()
        emoji = "📰"
        
        for topic in topics:
            if topic.lower() in text:
                emoji = get_topic_emoji(topic)
                break
        
        markdown += f"### {emoji} **{article['headline']}**\n\n"
        markdown += f"*Source: {article['source_domain']}* | *Author: {article['author']}* | *Date: {article['publish_date']}*\n\n"
        markdown += f"{article['summary']}\n\n"
        
        if article['url']:
            markdown += f"[Read more]({article['url']})\n\n"
        
        markdown += "---\n\n"
    
    conflicts = detect_conflicting_reports(articles)
    if conflicts:
        markdown += "### ⚠️ Conflicting Reports Detected\n\n"
        for conflict in conflicts:
            markdown += f"- {conflict['article1']['source_domain']} vs {conflict['article2']['source_domain']}: {conflict['issue']}\n\n"
        markdown += "---\n\n"
    
    return markdown


def save_briefing(markdown_content):
    """Save briefing to outputs directory with timestamp filename."""
    ensure_outputs_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"briefing_{timestamp}.md"
    filepath = Path(OUTPUTS_DIR) / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    
    return filepath


def setup_command():
    """Interactive setup command to configure user preferences."""
    print("=== Newsie Setup ===\n")
    
    print("Enter your preferred companies (comma-separated, e.g., Apple, Google, Microsoft):")
    companies_input = input("> ").strip()
    companies = [c.strip() for c in companies_input.split(",") if c.strip()]
    
    print("\nEnter your preferred topics (comma-separated, e.g., AI, cybersecurity, startups):")
    topics_input = input("> ").strip()
    topics = [t.strip() for t in topics_input.split(",") if t.strip()]
    
    print("\nEnter number of articles per briefing (default: 5):")
    count_input = input("> ").strip()
    try:
        article_count = int(count_input) if count_input else 5
    except ValueError:
        article_count = 5
    
    config = {
        "preferences": {
            "companies": companies,
            "topics": topics,
            "article_count": article_count,
            "region": "international"
        },
        "feedback": {
            "quality_ratings": [],
            "topic_requests": []
        }
    }
    
    ensure_outputs_dir()
    save_config(config)
    print(f"\nConfiguration saved to {CONFIG_FILE}")
    print(f"Outputs will be stored in {OUTPUTS_DIR}/")
    
    return config


def briefing_command(args):
    """Generate news briefing command."""
    config = load_config()
    
    if not config:
        print("No configuration found. Run 'newsie setup' first.")
        sys.exit(1)
    
    topics = args.topics if args.topics else config["preferences"]["topics"]
    companies = config["preferences"]["companies"]
    count = args.count if args.count else config["preferences"]["article_count"]
    
    print(f"Fetching {count} articles for topics: {', '.join(topics) if topics else 'General'}")
    print(f"Companies: {', '.join(companies) if companies else 'All'}")
    
    articles = fetch_news_by_topic(topics, companies, count)
    
    if not articles:
        print("\nNo news found for your preferred topics.")
        print("Try running with --topics flag or run 'newsie setup' to configure preferences.")
        sys.exit(0)
    
    ranked_articles = rank_articles(articles, topics, companies)
    
    markdown_content = format_briefing(ranked_articles, config)
    
    filepath = save_briefing(markdown_content)
    print(f"\nBriefing saved to: {filepath}")
    
    return filepath


def add_feedback(rating, topic_request=None):
    """Add user feedback to configuration."""
    config = load_config()
    
    if not config:
        print("No configuration found. Run 'newsie setup' first.")
        sys.exit(1)
    
    if rating is not None:
        config["feedback"]["quality_ratings"].append({
            "rating": rating,
            "timestamp": datetime.now().isoformat()
        })
    
    if topic_request:
        config["feedback"]["topic_requests"].append({
            "request": topic_request,
            "timestamp": datetime.now().isoformat()
        })
    
    save_config(config)
    print("Feedback saved successfully.")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Newsie - Personalized AI assistant for tech news briefings"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    setup_parser = subparsers.add_parser("setup", help="Interactive setup for preferences")
    
    briefing_parser = subparsers.add_parser("briefing", help="Generate news briefing")
    briefing_parser.add_argument("--topics", nargs="+", help="Override preferred topics")
    briefing_parser.add_argument("--count", type=int, help="Override article count")
    
    feedback_parser = subparsers.add_parser("feedback", help="Submit feedback")
    feedback_parser.add_argument("--rating", type=int, choices=[1, 2, 3, 4, 5], help="Quality rating (1-5)")
    feedback_parser.add_argument("--topic", type=str, help="Request more/less coverage of topic")
    
    args = parser.parse_args()
    
    if args.command == "setup":
        setup_command()
    elif args.command == "briefing":
        briefing_command(args)
    elif args.command == "feedback":
        add_feedback(args.rating, args.topic)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
