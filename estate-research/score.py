"""Clean, dedupe, score and tag the raw scan into library.json + summary.json.

Score is a longevity heuristic (days live, still running, duplicate copies),
not conversion data. Tags are keyword rules; swap in an LLM pass for nuance.
"""
import json, re, time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
RAW = HERE / "raw"
NOW = time.time()

NICHE = re.compile(r"estate plan|living trust|revocable trust|\btrusts?\b|\bwills?\b|probate|"
                   r"power of attorney|elder law|medicaid|nursing home|asset protection|"
                   r"inheritance|heirs|legacy plan", re.I)
JUNK = re.compile(r"real estate agent|realtor|homes? for sale|mortgage rate|crypto|forex", re.I)

FORMATS = {
    "webinar": r"webinar|online (class|workshop|event)|zoom|virtual (seminar|workshop|event)|livestream",
    "seminar": r"seminar|in[- ]person|workshop|lunch(eon)?|dinner|breakfast|library|community center|seats? (are )?limited",
    "free_consult": r"free (consult|consultation|strategy session|review|call)",
    "guide": r"free (guide|ebook|e-book|checklist|report|kit|download)",
}
ANGLES = {
    "avoid_probate": r"probate",
    "nursing_home_medicaid": r"nursing home|medicaid|long[- ]term care",
    "protect_family": r"your (family|children|kids|loved ones)|fight(ing)? over|family feud",
    "taxes": r"\btax(es)?\b|irs|estate tax|capital gains",
    "fear_of_state": r"the (state|court|government) (decides|will decide|takes)|without a will",
    "blended_family": r"blended famil|second marriage|stepchild",
    "home_protection": r"protect your home|lose (your|the) home|keep your home",
    "diy_mistakes": r"mistake|legalzoom|online will|diy",
    "retirees_age": r"\b(55|60|62|65)\+?|retire(e|ment|d)|seniors?",
}
HOOKS = {
    "question": r"^[^.!\n]{0,120}\?",
    "number": r"^\W*\d",
    "warning": r"^\W*(warning|attention|don'?t|stop|avoid)",
    "local": r"\b(near you|in your area|county|local)\b",
    "urgency": r"seats? (are )?limited|spots? (are )?limited|only \d+|filling (up )?fast|this (week|thursday|saturday)|register (now|today)",
}


def text_of(ad):
    s = ad.get("snapshot") or {}
    parts = [((s.get("body") or {}).get("text") if isinstance(s.get("body"), dict) else s.get("body")),
             s.get("title"), s.get("linkDescription"), s.get("caption"), s.get("ctaText")]
    for c in s.get("cards") or []:
        parts += [c.get("body"), c.get("title"), c.get("linkDescription")]
    return "\n".join(p for p in parts if isinstance(p, str))


def media_of(ad):
    s = ad.get("snapshot") or {}
    imgs = [i.get("originalImageUrl") or i.get("resizedImageUrl") for i in s.get("images") or []]
    vids = [v.get("videoPreviewImageUrl") for v in s.get("videos") or []]
    cards = [c.get("originalImageUrl") or c.get("videoPreviewImageUrl") for c in s.get("cards") or []]
    kind = "video" if s.get("videos") or any(c.get("videoHdUrl") or c.get("videoSdUrl") for c in s.get("cards") or []) \
        else "carousel" if len(s.get("cards") or []) > 1 else "image"
    return kind, [u for u in imgs + vids + cards if u][:3]


def ts(v):
    if isinstance(v, (int, float)):
        return v / 1000 if v > 1e11 else v
    if isinstance(v, str) and v[:4].isdigit():
        return time.mktime(time.strptime(v[:10], "%Y-%m-%d"))
    return None


def tags(rules, text):
    return [k for k, rx in rules.items() if re.search(rx, text, re.I | re.M)]


def main():
    raw = []
    for f in sorted(RAW.glob("pass*.json")):
        raw += json.loads(f.read_text())
    seen, lib = set(), []
    for ad in raw:
        aid = str(ad.get("adArchiveID") or ad.get("adArchiveId") or ad.get("adId") or "")
        txt = text_of(ad)
        if not aid or aid in seen or not NICHE.search(txt) or JUNK.search(txt):
            continue
        seen.add(aid)
        start, end = ts(ad.get("startDate")), ts(ad.get("endDate"))
        live = bool(ad.get("isActive"))
        days = max(0, int(((NOW if live or not end else end) - start) / 86400)) if start else 0
        copies = int(ad.get("collationCount") or 1)
        score = min(100, round(days / 180 * 60 + (25 if live else 0) + min(copies, 15)))
        kind, media = media_of(ad)
        lib.append({
            "id": aid, "page": ad.get("pageName"), "pageId": str(ad.get("pageID") or ""),
            "text": txt[:1200], "cta": (ad.get("snapshot") or {}).get("ctaText"),
            "link": (ad.get("snapshot") or {}).get("linkUrl"), "media": media, "kind": kind,
            "days": days, "live": live, "copies": copies, "score": score,
            "proven": days >= 90 and live,
            "formats": tags(FORMATS, txt), "angles": tags(ANGLES, txt), "hooks": tags(HOOKS, txt),
            "url": f"https://www.facebook.com/ads/library/?id={aid}",
        })
    lib.sort(key=lambda a: a["score"], reverse=True)
    (HERE / "library.json").write_text(json.dumps(lib, indent=1))

    event = [a for a in lib if {"webinar", "seminar"} & set(a["formats"])]
    cnt = lambda key, pool: Counter(t for a in pool for t in a[key]).most_common()
    costs = json.loads((RAW / "costs.json").read_text()) if (RAW / "costs.json").exists() else {}
    summary = {
        "scanned": len(raw), "kept": len(lib), "advertisers": len({a["page"] for a in lib}),
        "proven": sum(a["proven"] for a in lib),
        "event_ads": len(event), "event_advertisers": len({a["page"] for a in event}),
        "event_proven": sum(a["proven"] for a in event),
        "formats": cnt("formats", lib), "angles_all": cnt("angles", lib),
        "angles_event": cnt("angles", event), "hooks_event": cnt("hooks", event),
        "media_event": Counter(a["kind"] for a in event).most_common(),
        "top_event_advertisers": Counter(a["page"] for a in event).most_common(15),
        "longest_running_event_ad_days": max((a["days"] for a in event), default=0),
        "cost_usd": round(sum(costs.values()), 2),
    }
    (HERE / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps({k: v for k, v in summary.items() if not isinstance(v, list)}, indent=2))


if __name__ == "__main__":
    main()
