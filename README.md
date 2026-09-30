# Evergreen Lead Gen

The ad-research-to-launch workflow we built for a college consultant, as two static pages you can read, fork and deploy.

- **`launch/`** is the walkthrough page: results-focused sections, the ad kit, the research findings, a "what one client is worth" calculator, and a booking section. Open `launch/index.html` in a browser or deploy the folder as-is (any static host).
  - Personalize it per viewer with query params: `?first=Sarah&company=Acme&type=webinar|workshop|guide|none&front=Title&area=in%20Fairfield%20County`. `link.html` builds the URL for you.
  - Edit `launch/data.js` for the booking link, the offer band and, once you have real numbers, the results scene.
  - `launch/source/` holds the template and build script. It expects a `site/` output folder next to it, so treat it as reference.
- **`guide/`** is the how-to: scrape competitor ads with Apify, score them by how long they survive, tag angles, learn the patterns, brief creatives with an LLM, generate statics and reels, and launch with the right tracking. Open `guide/index.html`.

## Notes
- Competitor ad screenshots used on the live page (`img/lib-*.jpg`) are third-party creative and are not included here. Replace them with screenshots from your own research.
- Figures shown (721 ads scanned, 40 proven, 26 ads, $4.36 in scraping) are research findings from one scan, not campaign results.
- Ad-library scores are a longevity heuristic, not conversion data.
