import csv

def write_csv_report(page_data, filename="report.csv"):
    """Write page data to a CSV file.
    
    Args:
        page_data: Dictionary of page data (keys are normalized URLs)
        filename: Output CSV filename (default: report.csv)
    """
    fieldnames = ["page_url", "h1", "first_paragraph", "outgoing_link_urls", "image_urls"]
    
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for page in page_data.values():
            # Skip pages with errors
            if "error" in page:
                continue
                
            row = {
                "page_url": page.get("url", ""),
                "h1": page.get("h1", ""),
                "first_paragraph": page.get("first_paragraph", ""),
                "outgoing_link_urls": ";".join(page.get("outgoing_links", [])),
                "image_urls": ";".join(page.get("image_urls", []))
            }
            writer.writerow(row)