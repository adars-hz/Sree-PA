"""
Free Web Search Service for Project SREE
Queries open search results via DuckDuckGo without paid API keys.
"""

import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import logging

logger = logging.getLogger("sree.search")

class WebSearchService:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        Fetches live web search results using DuckDuckGo HTML.
        Returns a list of dicts with 'title', 'snippet', and 'url'.
        """
        clean_query = query.strip()
        if not clean_query:
            return []

        url = "https://html.duckduckgo.com/html/"
        data = {"q": clean_query}

        try:
            async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
                resp = await client.post(url, data=data, headers=self.headers)
                if resp.status_code != 200:
                    logger.warning(f"DuckDuckGo search returned status {resp.status_code}")
                    return []

                soup = BeautifulSoup(resp.text, "html.parser")
                results = []

                for r in soup.find_all("div", class_="result", limit=max_results * 2):
                    title_elem = r.find("a", class_="result__a")
                    snippet_elem = r.find("a", class_="result__snippet")
                    
                    if title_elem and snippet_elem:
                        title = title_elem.get_text(strip=True)
                        snippet = snippet_elem.get_text(strip=True)
                        link = title_elem.get("href", "")
                        
                        results.append({
                            "title": title,
                            "snippet": snippet,
                            "url": link
                        })
                        if len(results) >= max_results:
                            break

                return results
        except Exception as e:
            logger.error(f"Search request failed: {e}")
            return []

web_search_service = WebSearchService()

