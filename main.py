import sys
import asyncio
import aiohttp
from urllib.parse import urlparse

from crawl import normalize_url, extract_page_data, get_urls_from_html
from csv_report import write_csv_report

class AsyncCrawler:
    def __init__(self, base_url: str, max_concurrency: int = 3, max_pages: int = 10):
        self.base_url = base_url
        self.base_domain = _get_domain_from_normalized(normalize_url(base_url))
        self.page_data = {}
        self.lock = asyncio.Lock()
        self.max_concurrency = max_concurrency
        self.max_pages = max_pages
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.session = None
        self.should_stop = False
        self.all_tasks = set()

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers={"User-Agent": "BootCrawler/1.0"})
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

    async def get_html(self, url: str) -> str:
        try:
            async with self.session.get(url, timeout=10) as resp:
                if resp.status >= 400:
                    raise RuntimeError(f"received status code {resp.status}")
                content_type = resp.headers.get("Content-Type", "")
                if not content_type.lower().startswith("text/html"):
                    raise RuntimeError(f"invalid content-type: {content_type!r}")
                return await resp.text()
        except asyncio.TimeoutError as exc:
            raise RuntimeError(f"timeout fetching {url}") from exc
        except Exception as exc:
            raise RuntimeError(f"failed to fetch {url}: {exc}") from exc

    async def crawl_page(self, url: str) -> None:
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
            
            print(f"Fetching: {url}")
            async with self.semaphore:
                try:
                    html = await self.get_html(url)
                except Exception as exc:
                    print(f"Error fetching {url}: {exc}")
                    async with self.lock:
                        self.page_data[current_norm] = {
                            "url": url,
                            "error": str(exc)
                        }
                    return
                
                try:
                    data = extract_page_data(html, url)
                    async with self.lock:
                        self.page_data[current_norm] = data
                except Exception as exc:
                    print(f"Error extracting data from {url}: {exc}")
                    async with self.lock:
                        self.page_data[current_norm] = {
                            "url": url,
                            "error": f"extract error: {exc}"
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
                        task = asyncio.create_task(self.crawl_page(new_url))
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

async def crawl_site_async(base_url: str, max_concurrency: int = 3, max_pages: int = 10) -> dict:
    async with AsyncCrawler(base_url, max_concurrency, max_pages) as crawler:
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