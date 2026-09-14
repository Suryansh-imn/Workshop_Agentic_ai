"""
Web research tools for the Strands agent.
All tools use the @tool decorator - docstrings become schemas.
"""

import time
import requests
from bs4 import BeautifulSoup


def fetch_url(url: str) -> str:
    """
    Fetch a URL and return its content.

    Args:
        url: The URL to fetch

    Returns:
        The page content
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        return f"Error fetching {url}: {str(e)}"


def clean_html(html: str) -> str:
    """
    Strip HTML tags and return clean text, limited to 6000 characters.

    Args:
        html: HTML content to clean

    Returns:
        Clean text, max 6000 chars
    """
    try:
        soup = BeautifulSoup(html, 'html.parser')
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        # Limit length
        return text[:6000]
    except Exception as e:
        return f"Error cleaning HTML: {str(e)}"


def hn_search(query: str, days_back: int = 7) -> str:
    """
    Search Hacker News for stories matching a query.

    Args:
        query: Search term
        days_back: How many days back to search (default 7)

    Returns:
        JSON string with search results
    """
    try:
        # Calculate timestamp for N days ago
        timestamp = int(time.time()) - (days_back * 24 * 60 * 60)

        url = f"https://hn.algolia.com/api/v1/search"
        params = {
            "query": query,
            "tags": "story",
            "numericFilters": f"created_at_i>{timestamp}"
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        hits = data.get("hits", [])

        # Format results
        results = []
        for hit in hits[:10]:  # Limit to 10
            results.append({
                "title": hit.get("title", ""),
                "url": hit.get("url", ""),
                "hn_url": f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                "author": hit.get("author", ""),
                "points": hit.get("points", 0),
                "num_comments": hit.get("num_comments", 0),
                "created_at": hit.get("created_at", "")
            })

        return f"Found {len(results)} stories:\n" + "\n".join([
            f"- {r['title']} ({r['points']} pts, {r['num_comments']} comments) {r['hn_url']}"
            for r in results
        ])

    except Exception as e:
        return f"Error searching HN: {str(e)}"
