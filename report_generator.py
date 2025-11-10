import json
from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict, Counter
from datetime import datetime


class ReportGenerator:
    """Generate various report formats from crawl data."""
    
    def __init__(self, page_data: Dict[str, Any], base_url: str):
        """
        Initialize the report generator.
        
        Args:
            page_data: Dictionary of page data from crawler
            base_url: Base URL of the crawled site
        """
        self.page_data = page_data
        self.base_url = base_url
        self.stats = self._calculate_statistics()
    
    def _calculate_statistics(self) -> Dict[str, Any]:
        """Calculate comprehensive statistics from page data."""
        total_pages = len(self.page_data)
        error_pages = sum(1 for p in self.page_data.values() if "error" in p)
        successful_pages = total_pages - error_pages
        
        if successful_pages == 0:
            return {
                "total_pages": total_pages,
                "successful_pages": 0,
                "error_pages": error_pages,
                "total_internal_links": 0,
                "total_external_links": 0,
                "avg_response_time": 0,
                "page_types": {},
                "depth_distribution": {},
                "avg_internal_links_per_page": 0,
                "avg_external_links_per_page": 0,
                "total_images": 0,
                "avg_images_per_page": 0
            }
        
        # Collect metrics
        response_times = []
        internal_link_counts = []
        external_link_counts = []
        image_counts = []
        page_types = []
        depths = []
        
        for page in self.page_data.values():
            if "error" not in page:
                if "response_time" in page:
                    response_times.append(page["response_time"])
                if "internal_link_count" in page:
                    internal_link_counts.append(page["internal_link_count"])
                if "external_link_count" in page:
                    external_link_counts.append(page["external_link_count"])
                if "image_count" in page:
                    image_counts.append(page["image_count"])
                if "page_type" in page:
                    page_types.append(page["page_type"])
                if "depth" in page:
                    depths.append(page["depth"])
        
        # Calculate statistics
        stats = {
            "total_pages": total_pages,
            "successful_pages": successful_pages,
            "error_pages": error_pages,
            "error_rate": (error_pages / total_pages * 100) if total_pages > 0 else 0,
            
            "total_internal_links": sum(internal_link_counts),
            "total_external_links": sum(external_link_counts),
            "avg_internal_links_per_page": sum(internal_link_counts) / len(internal_link_counts) if internal_link_counts else 0,
            "avg_external_links_per_page": sum(external_link_counts) / len(external_link_counts) if external_link_counts else 0,
            
            "total_images": sum(image_counts),
            "avg_images_per_page": sum(image_counts) / len(image_counts) if image_counts else 0,
            
            "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
            "min_response_time": min(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
            
            "page_types": dict(Counter(page_types)),
            "depth_distribution": dict(Counter(depths)),
            "max_depth": max(depths) if depths else 0
        }
        
        return stats
    
    def generate_json_report(self, output_path: str):
        """
        Generate a comprehensive JSON report.
        
        Args:
            output_path: Path to save the JSON file
        """
        report = {
            "metadata": {
                "base_url": self.base_url,
                "crawl_timestamp": datetime.now().isoformat(),
                "total_pages_crawled": len(self.page_data)
            },
            "statistics": self.stats,
            "pages": []
        }
        
        # Add page details
        for norm_url, data in self.page_data.items():
            page_info = {
                "normalized_url": norm_url,
                "url": data.get("url", norm_url),
                "depth": data.get("depth", 0),
                "page_type": data.get("page_type", "unknown"),
                "h1": data.get("h1", ""),
                "first_paragraph": data.get("first_paragraph", ""),
                "internal_link_count": data.get("internal_link_count", 0),
                "external_link_count": data.get("external_link_count", 0),
                "image_count": data.get("image_count", 0),
                "incoming_link_count": data.get("incoming_link_count", 0),
                "response_time": data.get("response_time", 0),
                "status_code": data.get("status_code", 0),
                "error": data.get("error", None)
            }
            
            # Optionally include links (can make the file large)
            if "internal_links" in data:
                page_info["internal_links"] = data["internal_links"][:50]  # Limit to first 50
            if "external_links" in data:
                page_info["external_links"] = data["external_links"][:50]
            
            report["pages"].append(page_info)
        
        # Save JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"JSON report saved to {output_path}")
    
    def generate_statistics_report(self, output_path: str):
        """
        Generate a plain text statistics report.
        
        Args:
            output_path: Path to save the text file
        """
        lines = [
            "=" * 60,
            "SITE ANALYSIS STATISTICS",
            "=" * 60,
            f"Base URL: {self.base_url}",
            f"Crawl Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "-" * 60,
            "OVERVIEW",
            "-" * 60,
            f"Total Pages Discovered: {self.stats['total_pages']}",
            f"Successfully Crawled: {self.stats['successful_pages']}",
            f"Errors: {self.stats['error_pages']} ({self.stats['error_rate']:.1f}%)",
            f"Maximum Depth: {self.stats['max_depth']}",
            "",
            "-" * 60,
            "LINK ANALYSIS",
            "-" * 60,
            f"Total Internal Links: {self.stats['total_internal_links']}",
            f"Total External Links: {self.stats['total_external_links']}",
            f"Avg Internal Links/Page: {self.stats['avg_internal_links_per_page']:.1f}",
            f"Avg External Links/Page: {self.stats['avg_external_links_per_page']:.1f}",
            "",
            "-" * 60,
            "PERFORMANCE",
            "-" * 60,
            f"Avg Response Time: {self.stats['avg_response_time']:.3f}s",
            f"Min Response Time: {self.stats['min_response_time']:.3f}s",
            f"Max Response Time: {self.stats['max_response_time']:.3f}s",
            "",
            "-" * 60,
            "CONTENT",
            "-" * 60,
            f"Total Images: {self.stats['total_images']}",
            f"Avg Images/Page: {self.stats['avg_images_per_page']:.1f}",
            "",
            "-" * 60,
            "PAGE TYPE DISTRIBUTION",
            "-" * 60,
        ]
        
        for page_type, count in sorted(self.stats['page_types'].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / self.stats['successful_pages'] * 100) if self.stats['successful_pages'] > 0 else 0
            lines.append(f"{page_type:20s}: {count:4d} ({percentage:5.1f}%)")
        
        lines.extend([
            "",
            "-" * 60,
            "DEPTH DISTRIBUTION",
            "-" * 60,
        ])
        
        for depth, count in sorted(self.stats['depth_distribution'].items()):
            percentage = (count / self.stats['total_pages'] * 100) if self.stats['total_pages'] > 0 else 0
            lines.append(f"Depth {depth:2d}: {count:4d} pages ({percentage:5.1f}%)")
        
        lines.append("=" * 60)
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"Statistics report saved to {output_path}")
        
        # Also print to console
        print('\n'.join(lines))
    
    def generate_html_report(self, output_path: str, graph_path: str = None):
        """
        Generate an HTML report.
        
        Args:
            output_path: Path to save the HTML file
            graph_path: Optional path to embedded graph visualization
        """
        # Get top pages by incoming links
        pages_by_importance = sorted(
            [p for p in self.page_data.values() if "error" not in p],
            key=lambda x: x.get("incoming_link_count", 0),
            reverse=True
        )[:20]
        
        # Get error pages
        error_pages = [p for p in self.page_data.values() if "error" in p]
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Site Analysis Report - {self.base_url}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
        }}
        .section {{
            background: white;
            padding: 25px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #667eea;
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            color: #666;
            font-size: 0.9em;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #667eea;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .url {{
            font-family: monospace;
            font-size: 0.9em;
            color: #0066cc;
        }}
        .error {{
            color: #d32f2f;
        }}
        .recommendations {{
            background-color: #e3f2fd;
            padding: 15px;
            border-left: 4px solid #2196f3;
            border-radius: 4px;
        }}
        .recommendations ul {{
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Site Analysis Report</h1>
        <p><strong>Base URL:</strong> {self.base_url}</p>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="section">
        <h2>Executive Summary</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{self.stats['total_pages']}</div>
                <div class="stat-label">Total Pages</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{self.stats['successful_pages']}</div>
                <div class="stat-label">Successfully Crawled</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{self.stats['total_internal_links']}</div>
                <div class="stat-label">Internal Links</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{self.stats['total_external_links']}</div>
                <div class="stat-label">External Links</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{self.stats['avg_response_time']:.2f}s</div>
                <div class="stat-label">Avg Response Time</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{self.stats['max_depth']}</div>
                <div class="stat-label">Maximum Depth</div>
            </div>
        </div>
    </div>
    
    <div class="section">
        <h2>Page Type Distribution</h2>
        <table>
            <thead>
                <tr>
                    <th>Page Type</th>
                    <th>Count</th>
                    <th>Percentage</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for page_type, count in sorted(self.stats['page_types'].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / self.stats['successful_pages'] * 100) if self.stats['successful_pages'] > 0 else 0
            html += f"""
                <tr>
                    <td>{page_type}</td>
                    <td>{count}</td>
                    <td>{percentage:.1f}%</td>
                </tr>
"""
        
        html += """
            </tbody>
        </table>
    </div>
    
    <div class="section">
        <h2>Most Important Pages (by incoming links)</h2>
        <table>
            <thead>
                <tr>
                    <th>URL</th>
                    <th>H1</th>
                    <th>Incoming Links</th>
                    <th>Type</th>
                    <th>Depth</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for page in pages_by_importance:
            html += f"""
                <tr>
                    <td class="url">{page['url']}</td>
                    <td>{page.get('h1', 'N/A')}</td>
                    <td>{page.get('incoming_link_count', 0)}</td>
                    <td>{page.get('page_type', 'unknown')}</td>
                    <td>{page.get('depth', 0)}</td>
                </tr>
"""
        
        html += """
            </tbody>
        </table>
    </div>
"""
        
        if error_pages:
            html += """
    <div class="section">
        <h2 class="error">Errors Encountered</h2>
        <table>
            <thead>
                <tr>
                    <th>URL</th>
                    <th>Error</th>
                </tr>
            </thead>
            <tbody>
"""
            for page in error_pages[:20]:  # Limit to first 20 errors
                html += f"""
                <tr>
                    <td class="url">{page['url']}</td>
                    <td class="error">{page.get('error', 'Unknown error')}</td>
                </tr>
"""
            html += """
            </tbody>
        </table>
    </div>
"""
        
        html += """
    <div class="section">
        <h2>Recommendations for Scraping</h2>
        <div class="recommendations">
            <h3>Key Observations:</h3>
            <ul>
"""
        
        # Add intelligent recommendations
        if self.stats['avg_response_time'] > 2.0:
            html += "                <li>Site has slow response times (>2s average). Consider implementing caching or reducing request frequency.</li>\n"
        
        if self.stats['error_rate'] > 10:
            html += f"                <li>High error rate ({self.stats['error_rate']:.1f}%). Review error pages and adjust crawling strategy.</li>\n"
        
        if self.stats['total_external_links'] > self.stats['total_internal_links']:
            html += "                <li>Site has more external than internal links. May be a portal or link directory.</li>\n"
        
        if self.stats['max_depth'] > 5:
            html += "                <li>Deep site structure detected. Consider setting depth limits for efficient crawling.</li>\n"
        
        # Page type specific recommendations
        if 'blog_post' in self.stats['page_types']:
            html += "                <li>Blog posts detected. Consider extracting publication dates and author information.</li>\n"
        
        if 'product' in self.stats['page_types']:
            html += "                <li>Product pages detected. Consider extracting prices, descriptions, and availability.</li>\n"
        
        html += """
            </ul>
        </div>
    </div>
    
</body>
</html>
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"HTML report saved to {output_path}")


def generate_all_reports(page_data: Dict[str, Any], base_url: str, output_dir: str):
    """
    Generate all report formats.
    
    Args:
        page_data: Dictionary of page data from crawler
        base_url: Base URL of the crawled site
        output_dir: Directory to save reports
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    generator = ReportGenerator(page_data, base_url)
    
    # Generate all reports
    generator.generate_json_report(str(output_path / "site_structure.json"))
    generator.generate_statistics_report(str(output_path / "statistics.txt"))
    generator.generate_html_report(str(output_path / "report.html"))
    
    return generator

