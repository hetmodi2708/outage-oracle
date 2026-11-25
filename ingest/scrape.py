import os
import re
import json
import requests
import trafilatura

README_URL = "https://raw.githubusercontent.com/danluu/post-mortems/master/README.md"
RAW_DIR = "data/raw"


### Step 1: Get the list of postmortem links from Dan Luu's README

def get_postmortem_links():
    """Download the README and pull out every [Company](url). summary line

    Returns:
        List of dicts with company, url, summary, section
    """
    readme = requests.get(README_URL, timeout=20).text

    links = []
    section = None

    for line in readme.splitlines():
        #Headings like "## Database" tell us which section we are in
        if line.startswith("## "):
            section = line[3:].strip()
            continue

        #Stop once we reach the sections that are not postmortems
        if section == "Other lists of postmortems":
            break

        #Lines look like: [Company](https://link). One-line summary
        match = re.match(r"\[(.*?)\]\((https?://\S+?)\)\.?\s*(.*)", line)
        if match:
            company, url, summary = match.groups()
            links.append({"company": company, "url": url, "summary": summary, "section": section})

    print(f"Found {len(links)} postmortem links")
    return links


### Step 2: Download one page and extract the main article text

def scrape_page(url):
    """Fetch a URL and return only the article text (no menus, ads, footers)"""
    response = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()  #turn 404 / 500 responses into an exception
    return trafilatura.extract(response.text)


### Step 3: Scrape every link and save each one as a JSON file

def scrape_all(links, min_chars=500):
    """Scrape all links and save them to data/raw/<number>_<company>.json"""
    os.makedirs(RAW_DIR, exist_ok=True)
    saved, skipped, failed = 0, 0, 0

    for i, link in enumerate(links):
        company_slug = re.sub(r"[^a-z0-9]+", "-", link["company"].lower()).strip("-")
        file_path = os.path.join(RAW_DIR, f"{i:03d}_{company_slug}.json")

        #Already scraped on a previous run -> skip it
        if os.path.exists(file_path):
            saved += 1
            continue

        print(f"[{i + 1}/{len(links)}] {link['company']}: {link['url']}")
        try:
            text = scrape_page(link["url"])
        except Exception as e:
            print(f"   Failed: {e}")
            failed += 1
            continue

        if not text or len(text) < min_chars:
            print(f"   Skipped: too little text")
            skipped += 1
            continue

        record = {**link, "text": text}
        #encoding="utf-8" matters on Windows, otherwise non-English characters crash the write
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        saved += 1

    print(f"\nSaved: {saved} | Skipped (too short): {skipped} | Failed (dead link): {failed}")


if __name__ == "__main__":
    links = get_postmortem_links()
    scrape_all(links)
