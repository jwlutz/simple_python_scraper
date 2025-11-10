# Site Analysis Tool

A tool for analyzing website structure before you build a scraper. Think of it as reconnaissance - you run this on a site to understand how it's organized, then use that knowledge to build an effective scraper.

## What It Does

Point it at a website and it will:
- Crawl the site and map out its structure
- Show you which pages are important (based on how many other pages link to them)
- Generate an interactive graph visualization of the site
- Categorize pages (blog posts, products, static pages, etc.)
- Give you detailed reports in JSON, HTML, and CSV
- Provide recommendations for scraping strategies

Perfect for planning scrapers for financial sites (SEC filings, stock data), content sites (blogs, news), or anything else you want to scrape systematically.

## Installation

```bash
git clone https://github.com/jwlutz/scraper.git
cd scraper
uv sync

# Or with pip
pip install -e .
```

## Quick Start

```bash
# Run a quick scan
python analyze.py https://example.com --preset quick_scan

# Results are saved to output/example_com_TIMESTAMP/
# Open report.html to see the analysis
```

## Real Examples

### Analyze SEC EDGAR for Financial Data Scraping
```bash
python analyze.py https://www.sec.gov/cgi-bin/browse-edgar \
  --rate-limit 1.0 \
  --max-pages 100 \
  --output analysis/sec
```

This shows you filing structures, company search patterns, and how to navigate the archive.

### UCLA Dining Menus
```bash
python analyze.py https://menu.dining.ucla.edu \
  --max-pages 50 \
  --output analysis/ucla_dining
```

Maps out menu pages so you can extract nutrition data systematically.

### Stock Data Sites
```bash
python analyze.py https://finviz.com \
  --preset polite_crawl \
  --output analysis/finviz
```

## What You Get

Each run creates a timestamped directory with:

- `report.html` - Human-readable analysis with statistics and recommendations
- `graph_interactive.html` - Click around and explore the site structure
- `site_structure.json` - Complete data for building your scraper
- `statistics.txt` - Quick overview of what was found

## Common Options

```bash
# Control how much to crawl
python analyze.py URL --max-pages 200 --max-depth 3

# Be polite (slower, fewer concurrent requests)
python analyze.py URL --rate-limit 1.0 --max-concurrency 2

# Just generate specific outputs
python analyze.py URL --formats json graph

# Custom output location
python analyze.py URL -o my_analysis
```

## Configuration

Edit `config.yaml` to set defaults, or use command-line flags to override.

Three presets available:
- `quick_scan` - Fast, 20 pages, depth 2
- `deep_analysis` - Thorough, 500 pages, unlimited depth
- `polite_crawl` - Slow and respectful, good for production sites

## Use With Docker

```bash
docker-compose build
docker-compose run analyzer https://example.com --preset quick_scan
```

## Features

**Crawling**
- Async for speed, configurable concurrency
- Automatic retries with exponential backoff
- Rate limiting to be polite
- Respects timeouts and handles errors gracefully

**Analysis**
- Classifies links as internal vs external
- Tracks page depth from the homepage
- Identifies page types automatically
- Calculates page importance by incoming links
- Records response times and errors

**Visualization**
- Interactive graphs showing site structure
- Node size = importance (more incoming links = bigger)
- Color by depth or page type
- Export to GraphML for use in other tools

**Reporting**
- HTML report with executive summary
- JSON export with complete data
- CSV for spreadsheet analysis
- Text statistics for quick review
- Recommendations for scraping strategies

## Typical Workflow

1. **Analyze the site**: `python analyze.py URL --preset quick_scan`
2. **Review the reports**: Look at `report.html` and explore the graph
3. **Identify patterns**: Note URL structures, page types, navigation
4. **Build your scraper**: Use the insights to target the right pages
5. **Iterate**: Re-analyze as needed to understand deeper sections

## Why This Exists

I built this for Boot.dev's web scraping project, then extended it to help plan scrapers for:
- UCLA dining data (track nutrition info)
- SEC EDGAR filings (extract financial data)
- Stock market sites (collect time series)
- Any site where I need to understand structure before scraping

It's the reconnaissance phase - understand before you build.

## Examples Included

- `examples/scheduler_example.py` - Run periodic analysis
- `examples/basic_analysis.sh` - Common usage patterns

## Running Tests

```bash
python -m pytest
```

## What's Next

After running this on a site, you'll have:
- Visual map of the site structure
- List of important pages to target
- URL patterns to match
- Understanding of how content is organized

Use that to build a focused, efficient scraper for just the data you need.

## Notes

- Start with small page limits to get a feel for the site
- Use rate limiting on production sites to be respectful
- The JSON export has everything - use it programmatically
- The graph visualization is great for understanding complex sites

Built with: aiohttp, BeautifulSoup, NetworkX, Plotly, Pyvis, Rich
