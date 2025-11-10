#!/bin/bash
# Basic site analysis examples

echo "Site Analysis Tool - Example Usage"
echo "===================================="
echo ""

# Example 1: Quick scan
echo "Example 1: Quick scan of a small site"
echo "Command: python analyze.py https://example.com --preset quick_scan"
echo ""

# Example 2: Deep analysis
echo "Example 2: Deep analysis with more pages"
echo "Command: python analyze.py https://example.com --max-pages 500 --max-concurrency 10"
echo ""

# Example 3: Polite crawling with rate limiting
echo "Example 3: Polite crawling with rate limiting"
echo "Command: python analyze.py https://example.com --rate-limit 1.0 --max-concurrency 2"
echo ""

# Example 4: Custom output directory
echo "Example 4: Save to custom directory"
echo "Command: python analyze.py https://example.com -o my_analysis"
echo ""

# Example 5: Generate only specific reports
echo "Example 5: Generate only JSON and HTML reports"
echo "Command: python analyze.py https://example.com --formats json html"
echo ""

# Example 6: Docker usage
echo "Example 6: Run with Docker"
echo "Command: docker-compose run analyzer https://example.com --preset quick_scan"
echo ""

echo "For more options, run: python analyze.py --help"

