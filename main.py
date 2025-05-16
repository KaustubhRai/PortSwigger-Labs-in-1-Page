#!/usr/bin/env python3
import os, requests
from bs4 import BeautifulSoup

# ─── CONFIG ───────────────────────────────────────────────────────────────────
BASE_URL      = "https://portswigger.net"
ALL_LABS_PATH = "/web-security/all-labs"
ROOT          = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR  = os.path.join(ROOT, "labs")
TEMPLATE_FILE = os.path.join(ROOT, "ResultTemplate.html")
OUTPUT_FILE   = os.path.join(ROOT, "PortSwiggerAllLabs.html")
# ───────────────────────────────────────────────────────────────────────────────

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# 1) fetch lab links
r = requests.get(BASE_URL + ALL_LABS_PATH); r.raise_for_status()
soup = BeautifulSoup(r.text, "html.parser")
links = [BASE_URL + a["href"] for a in soup.select(".widgetcontainer-lab-link a")]
print(f"Found {len(links)} labs")

# 2) download each lab
downloaded = []
for idx, url in enumerate(links, start=1):
    resp = requests.get(url)
    if resp.status_code != 200:
        print(f"Failed: {url}")
        continue
    slug = url.rstrip("/").split("/")[-1]
    fname = f"{idx:03d}-{slug}.html"
    path = os.path.join(DOWNLOAD_DIR, fname)
    # ensure uniqueness
    base, ext = os.path.splitext(path)
    i = 1
    while os.path.exists(path):
        path = f"{base}_{i}{ext}"
        i += 1
    with open(path, "wb") as f:
        f.write(resp.content)
    downloaded.append(path)
    print(f"  → {os.path.basename(path)}")

# 3) assemble into one HTML
combined = []
for path in downloaded:
    page = BeautifulSoup(open(path, encoding="utf-8"), "html.parser")
    for sec in page.select("div.section.theme-white"):
        # skip expert labs
        if sec.select_one(".label-purple-small"):
            continue
        # strip unwanted
        for cls in ("share-right","footer","hidden pageloadingmask"):
            el = sec.find(class_=cls)
            if el: el.decompose()
        # remove community solutions
        for sol in sec.select(".component-solution.expandable-container"):
            if "Community solutions" in sol.text:
                sol.decompose()
                break
        html = sec.prettify()
        html = html.replace("<details>", "<details open>")
        html = html.replace('href="/', f'href="{BASE_URL}/')
        slug = os.path.basename(path).replace(".html","")
        html = html.replace("</h1>", f" ({slug})</h1>")
        combined.append(html)
        combined.append("<hr>")

body = "\n".join(combined)

# 4) inject into template & write output
template = open(TEMPLATE_FILE, encoding="utf-8").read()
out = template.replace("{{ content }}", body)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(out)

print(f"\n✅ All done. Open:\n{OUTPUT_FILE}")
