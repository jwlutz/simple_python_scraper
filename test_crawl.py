import unittest
from crawl import (
    normalize_url, 
    get_h1_from_html, 
    get_first_paragraph_from_html,
    get_urls_from_html,
    get_images_from_html,
    extract_page_data
)

class TestCrawl(unittest.TestCase):
    def test_normalize_url_strips_protocol(self):
        input_url = "https://blog.boot.dev/path"
        actual = normalize_url(input_url)
        expected = "blog.boot.dev/path"
        self.assertEqual(actual, expected)
        
    def test_normalize_url_strips_http(self):
        input_url = "http://blog.boot.dev/path"
        actual = normalize_url(input_url)
        expected = "blog.boot.dev/path"
        self.assertEqual(actual, expected)

    def test_normalize_url_strips_www(self):
        input_url = "https://www.blog.boot.dev/path"
        actual = normalize_url(input_url)
        expected = "blog.boot.dev/path"
        self.assertEqual(actual, expected)

    def test_normalize_url_strips_trailing_slash(self):
        input_url = "https://blog.boot.dev/path/"
        actual = normalize_url(input_url)
        expected = "blog.boot.dev/path"
        self.assertEqual(actual, expected)

    def test_normalize_url_capitalizes(self):
        input_url = "https://BLOG.boot.dev/path"
        actual = normalize_url(input_url)
        expected = "blog.boot.dev/path"
        self.assertEqual(actual, expected)

    def test_normalize_url_strips_port(self):
        input_url = "https://blog.boot.dev:3000/path"
        actual = normalize_url(input_url)
        expected = "blog.boot.dev/path"
        self.assertEqual(actual, expected)

    def test_normalize_url_strips_auth(self):
        input_url = "https://user:pass@blog.boot.dev/path"
        actual = normalize_url(input_url)
        expected = "blog.boot.dev/path"
        self.assertEqual(actual, expected)

    def test_normalize_url_strips_query_params(self):
        input_url = "https://blog.boot.dev/path?foo=bar&baz=qux"
        actual = normalize_url(input_url)
        expected = "blog.boot.dev/path"
        self.assertEqual(actual, expected)

    def test_get_h1_from_html_basic(self):
        input_body = '<html><body><h1>Test Title</h1></body></html>'
        actual = get_h1_from_html(input_body)
        expected = "Test Title"
        self.assertEqual(actual, expected)

    def test_get_h1_from_html_no_h1(self):
        input_body = '<html><body><h2>Not an h1</h2></body></html>'
        actual = get_h1_from_html(input_body)
        expected = ""
        self.assertEqual(actual, expected)

    def test_get_h1_from_html_with_nested_tags(self):
        input_body = '<html><body><h1>Title with <span>nested</span> tags</h1></body></html>'
        actual = get_h1_from_html(input_body)
        expected = "Title with nested tags"
        self.assertEqual(actual, expected)

    # Paragraph Tests
    def test_get_first_paragraph_from_html_main_priority(self):
        input_body = '''<html><body>
            <p>Outside paragraph.</p>
            <main>
                <p>Main paragraph.</p>
            </main>
        </body></html>'''
        actual = get_first_paragraph_from_html(input_body)
        expected = "Main paragraph."
        self.assertEqual(actual, expected)

    def test_get_first_paragraph_from_html_no_main(self):
        input_body = '''<html><body>
            <p>First paragraph.</p>
            <p>Second paragraph.</p>
        </body></html>'''
        actual = get_first_paragraph_from_html(input_body)
        expected = "First paragraph."
        self.assertEqual(actual, expected)

    def test_get_first_paragraph_from_html_no_paragraphs(self):
        input_body = '<html><body><div>Not a paragraph</div></body></html>'
        actual = get_first_paragraph_from_html(input_body)
        expected = ""
        self.assertEqual(actual, expected)

    def test_get_urls_from_html_absolute(self):
        input_url = "https://blog.boot.dev"
        input_body = '<html><body><a href="https://blog.boot.dev"><span>Boot.dev</span></a></body></html>'
        actual = get_urls_from_html(input_body, input_url)
        expected = ["https://blog.boot.dev"]
        self.assertEqual(actual, expected)

    def test_get_urls_from_html_relative(self):
        input_url = "https://blog.boot.dev"
        input_body = '<html><body><a href="/path/page.html">Page</a></body></html>'
        actual = get_urls_from_html(input_body, input_url)
        expected = ["https://blog.boot.dev/path/page.html"]
        self.assertEqual(actual, expected)

    def test_get_urls_from_html_multiple(self):
        input_url = "https://blog.boot.dev"
        input_body = '''
            <html><body>
                <a href="/path1">Link 1</a>
                <a href="https://example.com">Link 2</a>
                <a href="/path2">Link 3</a>
            </body></html>
        '''
        actual = get_urls_from_html(input_body, input_url)
        expected = [
            "https://blog.boot.dev/path1",
            "https://example.com",
            "https://blog.boot.dev/path2"
        ]
        self.assertEqual(actual, expected)

    # Image extraction tests
    def test_get_images_from_html_relative(self):
        input_url = "https://blog.boot.dev"
        input_body = '<html><body><img src="/logo.png" alt="Logo"></body></html>'
        actual = get_images_from_html(input_body, input_url)
        expected = ["https://blog.boot.dev/logo.png"]
        self.assertEqual(actual, expected)

    def test_get_images_from_html_absolute(self):
        input_url = "https://blog.boot.dev"
        input_body = '<html><body><img src="https://cdn.boot.dev/image.png"></body></html>'
        actual = get_images_from_html(input_body, input_url)
        expected = ["https://cdn.boot.dev/image.png"]
        self.assertEqual(actual, expected)

    def test_get_images_from_html_multiple_and_missing(self):
        input_url = "https://blog.boot.dev"
        input_body = '''
            <html><body>
                <img src="/img1.png" alt="First">
                <img>
                <img src="https://example.com/img2.jpg" alt="Second">
                <img src="/img3.png">
            </body></html>
        '''
        actual = get_images_from_html(input_body, input_url)
        expected = [
            "https://blog.boot.dev/img1.png",
            "https://example.com/img2.jpg",
            "https://blog.boot.dev/img3.png"
        ]
        self.assertEqual(actual, expected)

    def test_extract_page_data_basic(self):
        input_url = "https://blog.boot.dev"
        input_body = '''<html><body>
            <h1>Test Title</h1>
            <p>This is the first paragraph.</p>
            <a href="/link1">Link 1</a>
            <img src="/image1.jpg" alt="Image 1">
        </body></html>'''
        actual = extract_page_data(input_body, input_url)
        expected = {
            "url": "https://blog.boot.dev",
            "h1": "Test Title",
            "first_paragraph": "This is the first paragraph.",
            "outgoing_links": ["https://blog.boot.dev/link1"],
            "image_urls": ["https://blog.boot.dev/image1.jpg"]
        }
        self.assertEqual(actual, expected)

    def test_extract_page_data_empty(self):
        input_url = "https://blog.boot.dev"
        input_body = '<html><body></body></html>'
        actual = extract_page_data(input_body, input_url)
        expected = {
            "url": "https://blog.boot.dev",
            "h1": "",
            "first_paragraph": "",
            "outgoing_links": [],
            "image_urls": []
        }
        self.assertEqual(actual, expected)

    def test_extract_page_data_complex(self):
        input_url = "https://blog.boot.dev/articles"
        input_body = '''<html><body>
            <h1>Main Article</h1>
            <main>
                <p>First paragraph in main.</p>
                <p>Second paragraph.</p>
            </main>
            <p>Outside paragraph</p>
            <a href="https://example.com">External Link</a>
            <a href="/internal">Internal Link</a>
            <img src="https://cdn.example.com/img.png" alt="External Image">
            <img src="/local.jpg" alt="Local Image">
        </body></html>'''
        actual = extract_page_data(input_body, input_url)
        expected = {
            "url": "https://blog.boot.dev/articles",
            "h1": "Main Article",
            "first_paragraph": "First paragraph in main.",
            "outgoing_links": [
                "https://example.com",
                "https://blog.boot.dev/internal"
            ],
            "image_urls": [
                "https://cdn.example.com/img.png",
                "https://blog.boot.dev/local.jpg"
            ]
        }
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()