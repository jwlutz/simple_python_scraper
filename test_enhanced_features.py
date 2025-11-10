import unittest
from crawl import (
    get_domain_from_url,
    classify_link,
    categorize_page_type,
    get_classified_links
)
from visualizer import SiteGraphBuilder
from report_generator import ReportGenerator


class TestLinkClassification(unittest.TestCase):
    """Test link classification functionality."""
    
    def test_get_domain_from_url(self):
        """Test domain extraction from URLs."""
        test_cases = [
            ("https://example.com/path", "example.com"),
            ("http://www.example.com/path", "example.com"),
            ("https://sub.example.com/path", "sub.example.com"),
            ("https://example.com:8080/path", "example.com"),
            ("https://user:pass@example.com/path", "example.com"),
        ]
        
        for url, expected_domain in test_cases:
            with self.subTest(url=url):
                self.assertEqual(get_domain_from_url(url), expected_domain)
    
    def test_classify_link_internal(self):
        """Test internal link classification."""
        base_domain = "example.com"
        
        internal_links = [
            "https://example.com/page",
            "http://example.com/another",
            "https://www.example.com/page",
        ]
        
        for link in internal_links:
            with self.subTest(link=link):
                self.assertEqual(classify_link(link, base_domain), "internal")
    
    def test_classify_link_external(self):
        """Test external link classification."""
        base_domain = "example.com"
        
        external_links = [
            "https://other.com/page",
            "https://sub.example.com/page",  # Subdomain counts as different
            "https://notexample.com/page",
        ]
        
        for link in external_links:
            with self.subTest(link=link):
                self.assertEqual(classify_link(link, base_domain), "external")
    
    def test_get_classified_links(self):
        """Test classified links extraction from HTML."""
        html = '''
        <html><body>
            <a href="https://example.com/page1">Internal 1</a>
            <a href="/page2">Internal 2</a>
            <a href="https://other.com/page">External</a>
        </body></html>
        '''
        base_url = "https://example.com"
        
        result = get_classified_links(html, base_url)
        
        self.assertIn("internal", result)
        self.assertIn("external", result)
        self.assertIn("all", result)
        
        # Should have 2 internal links
        self.assertEqual(len(result["internal"]), 2)
        
        # Should have 1 external link
        self.assertEqual(len(result["external"]), 1)
        
        # All should be sum of internal and external
        self.assertEqual(len(result["all"]), 3)


class TestPageCategorization(unittest.TestCase):
    """Test page type categorization."""
    
    def test_categorize_blog_post(self):
        """Test blog post detection."""
        urls = [
            "https://example.com/blog/my-post",
            "https://example.com/post/another-article",
            "https://example.com/article/news",
            "https://example.com/news/breaking",
        ]
        
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(categorize_page_type(url), "blog_post")
    
    def test_categorize_product(self):
        """Test product page detection."""
        urls = [
            "https://example.com/product/widget",
            "https://example.com/item/12345",
            "https://example.com/shop/product-name",
        ]
        
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(categorize_page_type(url), "product")
    
    def test_categorize_listing(self):
        """Test listing page detection."""
        urls = [
            "https://example.com/category/electronics",
            "https://example.com/tag/python",
            "https://example.com/archive/2024",
        ]
        
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(categorize_page_type(url), "listing")
    
    def test_categorize_static(self):
        """Test static page detection."""
        urls = [
            "https://example.com/contact",
            "https://example.com/about",
            "https://example.com/faq",
        ]
        
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(categorize_page_type(url), "static")
    
    def test_categorize_search(self):
        """Test search page detection."""
        urls = [
            "https://example.com/search",
            "https://example.com/results?q=test",
        ]
        
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(categorize_page_type(url), "search")
    
    def test_categorize_document(self):
        """Test document detection."""
        urls = [
            "https://example.com/file.pdf",
            "https://example.com/document.doc",
            "https://example.com/archive.zip",
        ]
        
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(categorize_page_type(url), "document")
    
    def test_categorize_homepage(self):
        """Test homepage detection."""
        urls = [
            "https://example.com",
            "https://example.com/",
        ]
        
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(categorize_page_type(url), "homepage")
    
    def test_categorize_generic_page(self):
        """Test generic page categorization."""
        url = "https://example.com/some/random/path"
        self.assertEqual(categorize_page_type(url), "page")


class TestGraphBuilder(unittest.TestCase):
    """Test graph visualization builder."""
    
    def setUp(self):
        """Set up test data."""
        self.page_data = {
            "example.com": {
                "url": "https://example.com",
                "h1": "Home",
                "page_type": "homepage",
                "depth": 0,
                "incoming_link_count": 0,
                "internal_link_count": 2,
                "external_link_count": 1,
                "internal_links": [
                    "https://example.com/page1",
                    "https://example.com/page2"
                ],
                "external_links": ["https://other.com"],
                "response_time": 0.5
            },
            "example.com/page1": {
                "url": "https://example.com/page1",
                "h1": "Page 1",
                "page_type": "page",
                "depth": 1,
                "incoming_link_count": 1,
                "internal_link_count": 1,
                "external_link_count": 0,
                "internal_links": ["https://example.com/page2"],
                "external_links": [],
                "response_time": 0.3
            },
            "example.com/page2": {
                "url": "https://example.com/page2",
                "h1": "Page 2",
                "page_type": "page",
                "depth": 1,
                "incoming_link_count": 2,
                "internal_link_count": 0,
                "external_link_count": 0,
                "internal_links": [],
                "external_links": [],
                "response_time": 0.4
            }
        }
        self.base_url = "https://example.com"
    
    def test_graph_creation(self):
        """Test that graph is created correctly."""
        builder = SiteGraphBuilder(self.page_data, self.base_url)
        
        # Check nodes
        self.assertEqual(builder.graph.number_of_nodes(), 3)
        self.assertIn("example.com", builder.graph)
        self.assertIn("example.com/page1", builder.graph)
        self.assertIn("example.com/page2", builder.graph)
    
    def test_graph_edges(self):
        """Test that edges are created correctly."""
        builder = SiteGraphBuilder(self.page_data, self.base_url)
        
        # Check edges
        self.assertTrue(builder.graph.has_edge("example.com", "example.com/page1"))
        self.assertTrue(builder.graph.has_edge("example.com", "example.com/page2"))
        self.assertTrue(builder.graph.has_edge("example.com/page1", "example.com/page2"))
    
    def test_node_attributes(self):
        """Test that node attributes are set correctly."""
        builder = SiteGraphBuilder(self.page_data, self.base_url)
        
        home_node = builder.graph.nodes["example.com"]
        self.assertEqual(home_node["page_type"], "homepage")
        self.assertEqual(home_node["depth"], 0)
        self.assertFalse(home_node["error"])
    
    def test_error_nodes(self):
        """Test handling of error pages."""
        error_data = {
            "example.com/error": {
                "url": "https://example.com/error",
                "error": "404 Not Found",
                "depth": 1,
                "incoming_link_count": 0
            }
        }
        
        builder = SiteGraphBuilder(error_data, self.base_url)
        error_node = builder.graph.nodes["example.com/error"]
        
        self.assertTrue(error_node["error"])
    
    def test_get_statistics(self):
        """Test graph statistics calculation."""
        builder = SiteGraphBuilder(self.page_data, self.base_url)
        stats = builder.get_statistics()
        
        self.assertEqual(stats["total_nodes"], 3)
        self.assertEqual(stats["total_edges"], 3)
        self.assertIn("avg_in_degree", stats)
        self.assertIn("avg_out_degree", stats)
    
    def test_get_important_pages(self):
        """Test getting most important pages."""
        builder = SiteGraphBuilder(self.page_data, self.base_url)
        important = builder.get_important_pages(top_n=2)
        
        # page2 has the most incoming links (2)
        self.assertEqual(important[0]["url"], "https://example.com/page2")
        self.assertEqual(important[0]["incoming_links"], 2)


class TestReportGenerator(unittest.TestCase):
    """Test report generation."""
    
    def setUp(self):
        """Set up test data."""
        self.page_data = {
            "example.com": {
                "url": "https://example.com",
                "h1": "Home",
                "first_paragraph": "Welcome",
                "page_type": "homepage",
                "depth": 0,
                "incoming_link_count": 0,
                "internal_link_count": 2,
                "external_link_count": 1,
                "image_count": 5,
                "response_time": 0.5,
                "status_code": 200,
                "internal_links": ["https://example.com/page1"],
                "external_links": ["https://other.com"]
            },
            "example.com/page1": {
                "url": "https://example.com/page1",
                "h1": "Page 1",
                "first_paragraph": "Content",
                "page_type": "blog_post",
                "depth": 1,
                "incoming_link_count": 1,
                "internal_link_count": 0,
                "external_link_count": 0,
                "image_count": 2,
                "response_time": 0.3,
                "status_code": 200,
                "internal_links": [],
                "external_links": []
            },
            "example.com/error": {
                "url": "https://example.com/error",
                "error": "404 Not Found",
                "depth": 1,
                "incoming_link_count": 0
            }
        }
        self.base_url = "https://example.com"
    
    def test_statistics_calculation(self):
        """Test that statistics are calculated correctly."""
        generator = ReportGenerator(self.page_data, self.base_url)
        stats = generator.stats
        
        self.assertEqual(stats["total_pages"], 3)
        self.assertEqual(stats["successful_pages"], 2)
        self.assertEqual(stats["error_pages"], 1)
        self.assertEqual(stats["total_internal_links"], 2)
        self.assertEqual(stats["total_external_links"], 1)
        self.assertEqual(stats["total_images"], 7)
    
    def test_page_type_distribution(self):
        """Test page type distribution calculation."""
        generator = ReportGenerator(self.page_data, self.base_url)
        stats = generator.stats
        
        self.assertIn("homepage", stats["page_types"])
        self.assertIn("blog_post", stats["page_types"])
        self.assertEqual(stats["page_types"]["homepage"], 1)
        self.assertEqual(stats["page_types"]["blog_post"], 1)
    
    def test_depth_distribution(self):
        """Test depth distribution calculation."""
        generator = ReportGenerator(self.page_data, self.base_url)
        stats = generator.stats
        
        self.assertIn(0, stats["depth_distribution"])
        self.assertIn(1, stats["depth_distribution"])
        self.assertEqual(stats["max_depth"], 1)
    
    def test_response_time_stats(self):
        """Test response time statistics."""
        generator = ReportGenerator(self.page_data, self.base_url)
        stats = generator.stats
        
        self.assertGreater(stats["avg_response_time"], 0)
        self.assertEqual(stats["min_response_time"], 0.3)
        self.assertEqual(stats["max_response_time"], 0.5)
    
    def test_error_rate_calculation(self):
        """Test error rate calculation."""
        generator = ReportGenerator(self.page_data, self.base_url)
        stats = generator.stats
        
        expected_error_rate = (1 / 3) * 100  # 1 error out of 3 pages
        self.assertAlmostEqual(stats["error_rate"], expected_error_rate, places=1)


class TestEmptyDataHandling(unittest.TestCase):
    """Test handling of empty or minimal data."""
    
    def test_empty_graph(self):
        """Test graph builder with empty data."""
        builder = SiteGraphBuilder({}, "https://example.com")
        stats = builder.get_statistics()
        
        self.assertEqual(stats["total_nodes"], 0)
        self.assertEqual(stats["total_edges"], 0)
    
    def test_empty_report(self):
        """Test report generator with empty data."""
        generator = ReportGenerator({}, "https://example.com")
        stats = generator.stats
        
        self.assertEqual(stats["total_pages"], 0)
        self.assertEqual(stats["successful_pages"], 0)
    
    def test_all_errors(self):
        """Test report with all error pages."""
        error_data = {
            "example.com/error1": {
                "url": "https://example.com/error1",
                "error": "404 Not Found"
            },
            "example.com/error2": {
                "url": "https://example.com/error2",
                "error": "500 Server Error"
            }
        }
        
        generator = ReportGenerator(error_data, "https://example.com")
        stats = generator.stats
        
        self.assertEqual(stats["total_pages"], 2)
        self.assertEqual(stats["successful_pages"], 0)
        self.assertEqual(stats["error_pages"], 2)
        self.assertEqual(stats["error_rate"], 100.0)


if __name__ == "__main__":
    unittest.main()

