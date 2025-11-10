import sys
import asyncio
import aiohttp
import time
from urllib.parse import urlparse
from collections import defaultdict

from crawl import normalize_url, extract_page_data, get_urls_from_html
from csv_report import write_csv_report

class AsyncCrawler:
    def __init__(self, base_url: str, max_concurrency: int = 3, max_pages: int = 10, 
                 max_retries: int = 3, retry_delay: float = 1.0, rate_limit: float = 0):
        self.base_url = base_url
        self.base_domain = _get_domain_from_normalized(normalize_url(base_url))
        self.page_data = {}
        self.incoming_links = defaultdict(list)  # Track incoming links for each page
        self.page_depth = {}  # Track depth of each page from base URL
        self.lock = asyncio.Lock()
        self.max_concurrency = max_concurrency
        self.max_pages = max_pages
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.session = None
        self.should_stop = False
        self.all_tasks = set()

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def add_page_visit(self, normalized_url: str) -> bool:
        async with self.lock:
            if self.should_stop:
                return False
                
            if normalized_url in self.page_data:
                return False
                
            if len(self.page_data) >= self.max_pages:
                print(f"Reached maximum number of pages to crawl ({self.max_pages})")
                self.should_stop = True
                # Cancel all running tasks
                for task in self.all_tasks:
                    task.cancel()
                return False
                
            self.page_data[normalized_url] = {"url": normalized_url, "status": "pending"}
            return True

    async def apply_rate_limit(self):
        """Apply rate limiting if configured."""
        if self.rate_limit > 0:
            async with self.lock:
                current_time = time.time()
                time_since_last = current_time - self.last_request_time
                min_delay = 1.0 / self.rate_limit
                
                if time_since_last < min_delay:
                    await asyncio.sleep(min_delay - time_since_last)
                
                self.last_request_time = time.time()
    
    async def get_html(self, url: str) -> tuple[str, int, float]:
        """Fetch HTML with retry logic and return (html, status_code, response_time)."""
        last_exception = None
        
        for attempt in range(self.max_retries):
            start_time = time.time()
            try:
                # Apply rate limiting before request
                await self.apply_rate_limit()
                
                async with self.session.get(url, timeout=10) as resp:
                    status_code = resp.status
                    if resp.status >= 400:
                        raise RuntimeError(f"received status code {resp.status}")
                    content_type = resp.headers.get("Content-Type", "")
                    if not content_type.lower().startswith("text/html"):
                        raise RuntimeError(f"invalid content-type: {content_type!r}")
                    html = await resp.text()
                    response_time = time.time() - start_time
                    return html, status_code, response_time
                    
            except asyncio.TimeoutError as exc:
                last_exception = exc
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    print(f"Timeout fetching {url}, retrying in {delay:.1f}s (attempt {attempt + 1}/{self.max_retries})")
                    await asyncio.sleep(delay)
                    continue
                    
            except aiohttp.ClientError as exc:
                last_exception = exc
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    print(f"Network error fetching {url}, retrying in {delay:.1f}s (attempt {attempt + 1}/{self.max_retries})")
                    await asyncio.sleep(delay)
                    continue
                    
            except Exception as exc:
                # Don't retry on other exceptions (like content-type errors)
                raise RuntimeError(f"failed to fetch {url}: {exc}") from exc
        
        # All retries exhausted
        raise RuntimeError(f"failed to fetch {url} after {self.max_retries} attempts: {last_exception}") from last_exception

    async def crawl_page(self, url: str, depth: int = 0, parent_url: str = None) -> None:
        if self.should_stop:
            return

        try:
            current_norm = normalize_url(url)
            current_domain = _get_domain_from_normalized(current_norm)
            
            if current_domain != self.base_domain:
                print(f"Skipping {url} (different domain: {current_domain})")
                return
            if not await self.add_page_visit(current_norm):
                return
            
            # Track depth and incoming links
            async with self.lock:
                if current_norm not in self.page_depth:
                    self.page_depth[current_norm] = depth
                else:
                    self.page_depth[current_norm] = min(self.page_depth[current_norm], depth)
                
                if parent_url:
                    self.incoming_links[current_norm].append(parent_url)
            
            print(f"Fetching: {url} (depth: {depth})")
            async with self.semaphore:
                try:
                    html, status_code, response_time = await self.get_html(url)
                except Exception as exc:
                    print(f"Error fetching {url}: {exc}")
                    async with self.lock:
                        self.page_data[current_norm] = {
                            "url": url,
                            "error": str(exc),
                            "depth": depth,
                            "incoming_link_count": len(self.incoming_links[current_norm])
                        }
                    return
                
                try:
                    data = extract_page_data(html, url)
                    # Add additional metadata
                    data["status_code"] = status_code
                    data["response_time"] = response_time
                    data["depth"] = depth
                    data["incoming_links"] = self.incoming_links[current_norm].copy()
                    data["incoming_link_count"] = len(self.incoming_links[current_norm])
                    
                    async with self.lock:
                        self.page_data[current_norm] = data
                except Exception as exc:
                    print(f"Error extracting data from {url}: {exc}")
                    async with self.lock:
                        self.page_data[current_norm] = {
                            "url": url,
                            "error": f"extract error: {exc}",
                            "status_code": status_code,
                            "response_time": response_time,
                            "depth": depth,
                            "incoming_link_count": len(self.incoming_links[current_norm])
                        }
                    return
                
                if self.should_stop:
                    return
                    
                try:
                    urls = get_urls_from_html(html, url)
                    tasks = []
                    for new_url in urls:
                        if self.should_stop:
                            break
                        parsed = urlparse(new_url)
                        if parsed.scheme not in ("http", "https", ""):
                            continue
                        task = asyncio.create_task(self.crawl_page(new_url, depth=depth + 1, parent_url=url))
                        tasks.append(task)
                        self.all_tasks.add(task)
                    if tasks:
                        try:
                            await asyncio.gather(*tasks)
                        finally:
                            for task in tasks:
                                self.all_tasks.discard(task)
                except Exception as exc:
                    print(f"Error processing links from {url}: {exc}")
        
        except Exception as exc:
            print(f"Error crawling {url}: {exc}")

    async def crawl(self) -> dict:
        try:
            await self.crawl_page(self.base_url)
        except asyncio.CancelledError:
            print("Crawl cancelled")
        return self.page_data

async def crawl_site_async(base_url: str, max_concurrency: int = 3, max_pages: int = 10,
                          max_retries: int = 3, retry_delay: float = 1.0, rate_limit: float = 0) -> dict:
    async with AsyncCrawler(base_url, max_concurrency, max_pages, max_retries, retry_delay, rate_limit) as crawler:
        return await crawler.crawl()

def _get_domain_from_normalized(normalized_url: str) -> str:
    return normalized_url.split("/", 1)[0]

async def main_async():
    if len(sys.argv) < 2:
        print("no website provided")
        sys.exit(1)
    elif len(sys.argv) < 4:
        print("usage: uv run main.py URL max_concurrency max_pages")
        sys.exit(1)
    
    try:
        base_url = sys.argv[1]
        max_concurrency = int(sys.argv[2])
        max_pages = int(sys.argv[3])
    except ValueError:
        print("max_concurrency and max_pages must be integers")
        sys.exit(1)
        
    if max_concurrency < 1:
        print("max_concurrency must be at least 1")
        sys.exit(1)
    if max_pages < 1:
        print("max_pages must be at least 1")
        sys.exit(1)

    print(f"starting crawl of: {base_url}")
    print(f"max concurrent requests: {max_concurrency}")
    print(f"max pages to crawl: {max_pages}")
    
    page_data = await crawl_site_async(base_url, max_concurrency, max_pages)
    
    print(f"\nCrawl complete. Pages found: {len(page_data)}")
    print("Writing results to report.csv")
    write_csv_report(page_data)
    print("Report written to report.csv")

if __name__ == "__main__":
    asyncio.run(main_async())