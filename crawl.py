from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from typing import Dict, List, Tuple

def normalize_url(url):
    parsed = urlparse(url)
    netloc = parsed.netloc.lower()
    if '@' in netloc:
        netloc = netloc.split('@')[1]
    if ':' in netloc:
        netloc = netloc.split(':')[0]
    if netloc.startswith('www.'):
        netloc = netloc[4:]
    path = parsed.path
    if path.endswith('/'):
        path = path[:-1]
    return f"{netloc}{path}"

def get_domain_from_url(url: str) -> str:
    """Extract domain from a URL."""
    parsed = urlparse(url)
    netloc = parsed.netloc.lower()
    if '@' in netloc:
        netloc = netloc.split('@')[1]
    if ':' in netloc:
        netloc = netloc.split(':')[0]
    if netloc.startswith('www.'):
        netloc = netloc[4:]
    return netloc

def classify_link(url: str, base_domain: str) -> str:
    """Classify a link as internal or external."""
    link_domain = get_domain_from_url(url)
    return "internal" if link_domain == base_domain else "external"

def categorize_page_type(url: str, html: str = None) -> str:
    """Categorize page type based on URL patterns and content."""
    url_lower = url.lower()
    
    # Common patterns
    if any(x in url_lower for x in ['/blog/', '/post/', '/article/', '/news/']):
        return "blog_post"
    elif any(x in url_lower for x in ['/product/', '/item/', '/shop/']):
        return "product"
    elif any(x in url_lower for x in ['/category/', '/tag/', '/archive/']):
        return "listing"
    elif any(x in url_lower for x in ['/contact', '/about', '/faq']):
        return "static"
    elif any(x in url_lower for x in ['/search', '/results']):
        return "search"
    elif url_lower.endswith(('.pdf', '.doc', '.docx', '.zip', '.tar.gz')):
        return "document"
    elif url_lower.count('/') <= 3 and not url_lower.split('/')[-1]:
        return "homepage"
    else:
        return "page"

def get_h1_from_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    h1_tag = soup.find('h1')
    return h1_tag.get_text() if h1_tag else ""
    
def get_first_paragraph_from_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    main_tag = soup.find('main')
    if main_tag:
        p_tag = main_tag.find('p')
        if p_tag:
            return p_tag.get_text()
    p_tag = soup.find('p')
    return p_tag.get_text() if p_tag else ""

def get_urls_from_html(html, base_url):
    soup = BeautifulSoup(html, 'html.parser')
    urls = []
    for link in soup.find_all('a'):
        href = link.get('href')
        if href:
            absolute_url = urljoin(base_url, href)
            urls.append(absolute_url)

    return urls

def get_classified_links(html: str, base_url: str) -> Dict[str, List[str]]:
    """Get links classified as internal or external."""
    soup = BeautifulSoup(html, 'html.parser')
    base_domain = get_domain_from_url(base_url)
    
    internal_links = []
    external_links = []
    
    for link in soup.find_all('a'):
        href = link.get('href')
        if href:
            absolute_url = urljoin(base_url, href)
            if classify_link(absolute_url, base_domain) == "internal":
                internal_links.append(absolute_url)
            else:
                external_links.append(absolute_url)
    
    return {
        "internal": internal_links,
        "external": external_links,
        "all": internal_links + external_links
    }
    
def get_images_from_html(html, base_url):
    soup = BeautifulSoup(html, 'html.parser')
    image_urls = []
    for img in soup.find_all('img'):
        src = img.get('src')
        if src:
            absolute_url = urljoin(base_url, src)
            image_urls.append(absolute_url)
    return image_urls

def extract_page_data(html, page_url):
    classified_links = get_classified_links(html, page_url)
    
    return {
        "url": page_url,
        "h1": get_h1_from_html(html),
        "first_paragraph": get_first_paragraph_from_html(html),
        "outgoing_links": get_urls_from_html(html, page_url),
        "internal_links": classified_links["internal"],
        "external_links": classified_links["external"],
        "internal_link_count": len(classified_links["internal"]),
        "external_link_count": len(classified_links["external"]),
        "total_link_count": len(classified_links["all"]),
        "image_urls": get_images_from_html(html, page_url),
        "image_count": len(get_images_from_html(html, page_url)),
        "page_type": categorize_page_type(page_url, html)
    }