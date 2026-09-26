# The polite scraper — Books to Scrape pipeline

A small, polite scraping pipeline that downloads the first three catalogue pages of [Books to Scrape](https://books.toscrape.com), visits all 60 book pages, and turns the raw HTML into clean, schema-checked JSON — without crashing on a broken page, and with an honest report at the end of every run.

## Target Classification

- **Which site? :** https://books.toscrape.com
- **Why? :** It's an easy to work with sandbox site for me to develop basic scraper building skills.
- **How much? :** First three catalogue pages only (60 books total).
- **Data collected? :** Book title, price, availability status, star rating, product description, and product URL.
- **Is data appropriate? :** Yes, it is completely safe to scrape the data from the sandbox website, since its entire purpose is to serve as a testing site for scraping tools.
- **robots.txt result :** No robots file found.

> I will not reuse this code on another site without checking its rules and terms first.

## Lane & How to Run

**Lane:** Python (`requests` + `BeautifulSoup` + `pydantic`).

Install dependencies:

```bash
cd scraper
pip install -r requirements.txt
```

Run the pipeline (all paths are relative to `src/`, so run it from there):

```bash
cd src
python main.py
```

This produces:

- `src/output/books.json` — 60 validated book records
- `src/output/run-report.json` — a short report of what happened during the run
- `src/output/errors.json` — only created if a record fails schema validation
- `src/cache/` — cached HTML/JSON so re-running the script doesn't re-hit the site

Run it twice: the first run fetches and caches everything; the second run reads entirely from cache and produces the same 60 records, not 120.

## Record Schema

Each entry in `books.json` follows this shape (enforced with a Pydantic model before anything is stored):

| Field         | Type          | Meaning                                                                 |
|---------------|---------------|--------------------------------------------------------------------------|
| `id`          | `str`         | Canonical URL of the book page — used as the record's unique identity   |
| `title`       | `str`         | Book title                                                              |
| `product_url` | `str`         | Absolute URL of the book page (same value as `id`)                     |
| `price_text`  | `str`         | Human-readable price string, e.g. `"51.77 pounds"`                     |
| `price`       | `int \| float`| Numeric GBP price parsed from the page                                 |
| `availability`| `str`         | Raw availability text, e.g. `"In stock (22 available)"`                |
| `rating`      | `str`         | Star rating word taken from the page's CSS class, e.g. `"Three"`       |
| `description` | `str \| None` | Product description; `None` when the book page has no description     |
| `source_pg`   | `str`         | Catalogue page URL the book link was discovered on (provenance)        |
| `fetched_at`  | `str`         | ISO-8601 UTC timestamp of when the detail page was fetched             |

Records that fail this schema are written to `errors.json` with the validation reason and never make it into `books.json`.

## Politeness Rules

- **User-agent:** every real request sends an identifying string naming this project and linking back to this repo, so the site owner can see who's asking.
- **Delay:** the script waits 0.5s before every real network request. Cached pages skip the delay entirely, since they never leave the machine.
- **Timeout:** every request is capped at 30 seconds — it gives up instead of hanging forever.
- **Cache:** catalogue pages are cached as HTML under `src/cache/`, and individual book pages are cached as JSON under `src/cache/Books/`. Any URL that's already cached is read from disk instead of being fetched again.
- **Failure handling:** a 404 or 403 is not retried (the page doesn't exist, or the site said no); a timeout or 5xx gets exactly one retry after a short wait. Either way, one bad page is logged and skipped rather than crashing the run.

## Sample Run Report

A real `run-report.json` from a fully-cached run:

```json
{
    "start_time": "2026-09-26 19:35:49.688482",
    "duration": "0:00:00.337652",
    "pages_fetched": 0,
    "cache_hits": 63,
    "valid_records": 60,
    "invalid_records": 0,
    "failed_pages": 0
}
```

`cache_hits: 63` is the 3 catalogue pages plus 60 book pages, all served from the local cache instead of the live site.

## Why This Didn't Need a Browser

Books to Scrape renders every title, price, and description directly into the server's HTML response, so a plain HTTP `GET` already returns everything this scraper needs — a real browser (e.g. Playwright) would only add startup and rendering cost with no extra data to show for it.

## Known Limitation

The user-agent header is built with the key `"user_agent"` instead of the HTTP-standard `"User-Agent"`. The identifying string itself is correct, but because of that key name, `requests` likely never sends it as a header the target site actually recognizes as the User-Agent — so in practice this scraper is less identifiable to the site than it's meant to be. Everything else (delay, timeout, cache, failure handling) works as described above.

## Ethics Note

This project only scrapes Books to Scrape, a public sandbox built specifically so people can practice scraping on it — no real business, login, or paywall is involved. As a general rule going forward: use an official API instead of scraping whenever one exists, never bypass a login screen, paywall, or an explicit access block, and only collect the specific fields a task actually needs rather than an entire page.