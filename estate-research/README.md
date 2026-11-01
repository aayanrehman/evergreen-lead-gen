# Estate Planning Ad Scan

The Evergreen Ad Library method, re-aimed at estate planning firms, with weight on the ones running webinars and seminars (the segment on waterfallgrowth.com/estate).

```bash
export APIFY_TOKEN=...   # keep it out of git
python3 scrape.py        # 3 passes: keywords -> advertiser pages (seminar runners first) -> live image ads
python3 score.py         # niche filter, dedupe, longevity score, format/angle/hook tags
```

Outputs:
- `raw/pass*.json`: untouched Apify datasets (gitignored, Meta media links expire in ~a day, so download media you want to keep right away)
- `library.json`: one row per ad, sorted by score, feeds the library page and the video
- `summary.json`: the headline numbers (ads scanned, advertisers, proven event ads, top angles and hooks)

The score is a longevity heuristic (days live, still running, duplicate copies), not conversion data. "Proven" = live and running 90+ days.
