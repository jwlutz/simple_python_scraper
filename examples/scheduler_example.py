#!/usr/bin/env python3
"""
Example scheduler for periodic site analysis.

This script demonstrates how to schedule periodic crawls using the schedule library.
Install: pip install schedule
"""

import schedule
import time
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyze import run_analysis
import argparse


# Configuration
SITES_TO_MONITOR = [
    {
        "url": "https://example.com",
        "preset": "quick_scan",
        "schedule": "daily"  # Options: hourly, daily, weekly
    },
    # Add more sites here
]


def analyze_site(site_config):
    """Run analysis for a single site."""
    print(f"\n{'='*60}")
    print(f"Starting scheduled analysis: {site_config['url']}")
    print(f"{'='*60}\n")
    
    # Create args namespace
    args = argparse.Namespace(
        url=site_config['url'],
        config=None,
        preset=site_config.get('preset'),
        max_pages=None,
        max_concurrency=None,
        max_depth=None,
        timeout=None,
        max_retries=None,
        rate_limit=None,
        output='output',
        formats=['all'],
        no_visualization=False,
        quiet=False,
        verbose=False
    )
    
    try:
        asyncio.run(run_analysis(args))
        print(f"\nAnalysis completed successfully for {site_config['url']}")
    except Exception as e:
        print(f"\nError analyzing {site_config['url']}: {e}")


def schedule_jobs():
    """Schedule all configured jobs."""
    for site in SITES_TO_MONITOR:
        job_schedule = site.get('schedule', 'daily')
        
        if job_schedule == 'hourly':
            schedule.every().hour.do(analyze_site, site)
        elif job_schedule == 'daily':
            schedule.every().day.at("02:00").do(analyze_site, site)
        elif job_schedule == 'weekly':
            schedule.every().monday.at("02:00").do(analyze_site, site)
        
        print(f"Scheduled {job_schedule} analysis for {site['url']}")


def main():
    """Main scheduler loop."""
    print("Site Analysis Scheduler")
    print("=" * 60)
    
    if not SITES_TO_MONITOR:
        print("No sites configured. Edit scheduler_example.py to add sites.")
        return
    
    schedule_jobs()
    
    print(f"\nScheduler started. Monitoring {len(SITES_TO_MONITOR)} site(s).")
    print("Press Ctrl+C to stop.\n")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n\nScheduler stopped by user.")


if __name__ == "__main__":
    main()

