from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

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
    return {
        "url": page_url,
        "h1": get_h1_from_html(html),
        "first_paragraph": get_first_paragraph_from_html(html),
        "outgoing_links": get_urls_from_html(html, page_url),
        "image_urls": get_images_from_html(html, page_url)
    }