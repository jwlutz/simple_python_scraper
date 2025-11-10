"""
Browser-based crawler using Playwright for sites with aggressive bot detection.
Use this when regular HTTP requests get 403/blocked.
"""

import asyncio
from playwright.async_api import async_playwright, Page, Browser
from typing import Dict, Any
from collections import defaultdict
from crawl import normalize_url, extract_page_data


class BrowserCrawler:
    """Crawl sites using a real browser to bypass bot detection."""
    
    def __init__(self, base_url: str, max_pages: int = 50, max_depth: int = 3):
        self.base_url = base_url
        self.base_domain = self._get_domain(normalize_url(base_url))
        self.page_data = {}
        self.incoming_links = defaultdict(list)
        self.page_depth = {}
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.visited = set()
        self.browser = None
        self.context = None
        
    def _get_domain(self, normalized_url: str) -> str:
        """Extract domain from normalized URL."""
        return normalized_url.split("/", 1)[0]
    
    async def start_browser(self):
        """Start Playwright browser."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True  # Set to False to see the browser
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
    async def stop_browser(self):
        """Close browser."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def crawl_page(self, url: str, depth: int = 0, parent_url: str = None):
        """Crawl a single page with browser."""
        if depth > self.max_depth:
            return
        
        if len(self.page_data) >= self.max_pages:
            print(f"Reached max pages ({self.max_pages})")
            return
        
        current_norm = normalize_url(url)
        current_domain = self._get_domain(current_norm)
        
        # Skip if wrong domain or already visited
        if current_domain != self.base_domain:
            return
        
        if current_norm in self.visited:
            return
        
        self.visited.add(current_norm)
        
        # Track depth and incoming links
        if current_norm not in self.page_depth:
            self.page_depth[current_norm] = depth
        else:
            self.page_depth[current_norm] = min(self.page_depth[current_norm], depth)
        
        if parent_url:
            self.incoming_links[current_norm].append(parent_url)
        
        print(f"[{len(self.page_data)+1}/{self.max_pages}] Fetching: {url} (depth: {depth})")
        
        try:
            # Create new page
            page = await self.context.new_page()
            
            # Navigate with timeout
            response = await page.goto(url, timeout=30000, wait_until='domcontentloaded')
            
            # Get status code
            status_code = response.status if response else 0
            
            if status_code >= 400:
                self.page_data[current_norm] = {
                    "url": url,
                    "error": f"HTTP {status_code}",
                    "depth": depth,
                    "incoming_link_count": len(self.incoming_links[current_norm])
                }
                await page.close()
                return
            
            # Wait a bit for dynamic content
            await asyncio.sleep(0.5)
            
            # Get HTML content
            html = await page.content()
            
            # Extract page data
            data = extract_page_data(html, url)
            data["status_code"] = status_code
            data["depth"] = depth
            data["incoming_links"] = self.incoming_links[current_norm].copy()
            data["incoming_link_count"] = len(self.incoming_links[current_norm])
            data["response_time"] = 0  # Not tracking with browser
            
            self.page_data[current_norm] = data
            
            # Get links for further crawling
            if depth < self.max_depth and len(self.page_data) < self.max_pages:
                links = data.get("internal_links", [])
                
                # Crawl child pages sequentially (to avoid overwhelming the site)
                for link in links[:10]:  # Limit to first 10 links per page
                    if len(self.page_data) >= self.max_pages:
                        break
                    await self.crawl_page(link, depth + 1, url)
            
            await page.close()
            
        except Exception as e:
            print(f"Error crawling {url}: {e}")
            self.page_data[current_norm] = {
                "url": url,
                "error": str(e),
                "depth": depth,
                "incoming_link_count": len(self.incoming_links[current_norm])
            }
    
    async def crawl(self) -> Dict[str, Any]:
        """Start the crawl."""
        await self.start_browser()
        try:
            await self.crawl_page(self.base_url, depth=0)
        finally:
            await self.stop_browser()
        
        return self.page_data


async def crawl_with_browser(base_url: str, max_pages: int = 50, max_depth: int = 3) -> Dict[str, Any]:
    """Crawl a site using browser automation."""
    crawler = BrowserCrawler(base_url, max_pages, max_depth)
    return await crawler.crawl()

