"""Estate-planning ad scan: 3 passes over the Meta Ad Library via Apify.

Same method as the Evergreen (college consulting) scan, re-aimed at estate
planning firms, with extra weight on firms that run webinars and seminars.

    export APIFY_TOKEN=...            # never commit this
    python3 scrape.py                 # writes raw/pass1.json, raw/pass2.json, raw/pass3.json
    python3 score.py                  # writes library.json + summary.json

Cost is roughly $0.006 per ad. The defaults below cap a full run near 900 ads (~$5).
"""
import json, os, sys, time, urllib.parse, urllib.request
from pathlib import Path

TOKEN = os.environ.get("APIFY_TOKEN") or sys.exit("Set APIFY_TOKEN first.")
ACTOR = "apify~facebook-ads-scraper"
OUT = Path(__file__).parent / "raw"
OUT.mkdir(exist_ok=True)

# Pass 1: niche phrases. Seminar/webinar phrases come first because that's the
# segment we're selling into (waterfallgrowth.com/estate).
KEYWORDS = [
    "estate planning webinar", "estate planning seminar", "estate planning workshop",
    "free estate planning seminar", "living trust seminar", "living trust webinar",
    "trust and will workshop", "avoid probate seminar", "medicaid planning seminar",
    "asset protection seminar", "elder law seminar", "estate planning attorney",
    "revocable living trust", "avoid probate", "estate planning lawyer",
    "will and trust attorney", "protect your assets from nursing home",
]
PER_KEYWORD = 30      # pass 1 cap per URL
PER_PAGE = 25         # pass 2 cap per advertiser page
MAX_PAGES = 20        # pass 2: how many advertiser pages to expand
PER_IMAGE_QUERY = 20  # pass 3 cap per URL
COUNTRY = "US"


def library_url(q=None, page_id=None, media="all", active="all"):
    p = {"active_status": active, "ad_type": "all", "country": COUNTRY, "media_type": media,
         "sort_data[mode]": "total_impressions", "sort_data[direction]": "desc"}
    if page_id:
        p.update(view_all_page_id=page_id, search_type="page")
    else:
        p.update(q=q, search_type="keyword_unordered")
    return "https://www.facebook.com/ads/library/?" + urllib.parse.urlencode(p)


def api(path, body=None):
    req = urllib.request.Request(
        f"https://api.apify.com/v2/{path}",
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
        method="POST" if body is not None else "GET")
    return json.load(urllib.request.urlopen(req, timeout=120))


def run(urls, limit, name):
    print(f"[{name}] {len(urls)} URLs x {limit} ads")
    r = api(f"acts/{ACTOR}/runs", {"startUrls": [{"url": u} for u in urls], "resultsLimit": limit})["data"]
    while r["status"] in ("READY", "RUNNING"):
        time.sleep(15)
        r = api(f"actor-runs/{r['id']}")["data"]
        print(f"  {r['status']} ...", flush=True)
    items = api(f"datasets/{r['defaultDatasetId']}/items?clean=true&format=json")
    cost = (r.get("usageTotalUsd") or 0)
    print(f"[{name}] {r['status']}: {len(items)} ads, ${cost:.2f}")
    (OUT / f"{name}.json").write_text(json.dumps(items))
    return items, cost


def main():
    costs = {}
    p1, costs["pass1"] = run([library_url(q=k) for k in KEYWORDS], PER_KEYWORD, "pass1")

    # Pass 2: expand the advertisers pass 1 surfaced, seminar/webinar runners first.
    hot = ("webinar", "seminar", "workshop", "masterclass", "class", "event", "rsvp", "reserve")
    pages = {}
    for ad in p1:
        pid = str(ad.get("pageID") or ad.get("pageId") or "")
        if not pid:
            continue
        text = json.dumps(ad.get("snapshot", {})).lower()
        pages.setdefault(pid, [0, 0])
        pages[pid][0] += 1
        pages[pid][1] += any(h in text for h in hot)
    ranked = sorted(pages, key=lambda k: (pages[k][1], pages[k][0]), reverse=True)[:MAX_PAGES]
    p2, costs["pass2"] = run([library_url(page_id=p) for p in ranked], PER_PAGE, "pass2")

    # Pass 3: live image-only ads, the statics we can borrow structure from.
    img_q = ["estate planning seminar", "living trust", "estate planning attorney", "avoid probate"]
    p3, costs["pass3"] = run([library_url(q=k, media="image", active="active") for k in img_q],
                             PER_IMAGE_QUERY, "pass3")

    (OUT / "costs.json").write_text(json.dumps(costs, indent=2))
    print("total ads:", len(p1) + len(p2) + len(p3), "| cost: $%.2f" % sum(costs.values()))


if __name__ == "__main__":
    main()
