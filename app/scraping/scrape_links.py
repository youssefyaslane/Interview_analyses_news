# app/link_scraper.py
import time
import re
from typing import List, Dict
from seleniumbase import Driver

from app.Database.db import upsert_link  # import relatif vers ta DB
from app.scraping.utils import (
    clean_text,
    wait_for_dom_ready,
    click_cookie_banner_if_present,
    slow_scroll,
)

START_URLS = [
    "https://www.ft.com/",
    "https://www.ft.com/world",
    "https://www.ft.com/companies",
    "https://www.ft.com/markets",
    "https://www.ft.com/technology",
    "https://www.ft.com/opinion",
]

TITLE_LINK_SELECTORS = [
    "a.js-teaser-heading-link",
    "a[data-trackable='heading-link']",
    "a.o-teaser__heading",
    "a.o-teaser__heading-link",
    "a[data-trackable='teaser-link']",
]

SUMMARY_SELECTORS = [
    ".o-teaser__standfirst",
    "p.o-typography-summary",
    "p",
]

def _extract_teasers_from_page(driver: Driver, base_url: str) -> List[Dict]:
    items = []
    seen = set()

    for link_sel in TITLE_LINK_SELECTORS:
        try:
            links = driver.find_elements(link_sel)
        except Exception:
            links = []
        for a in links:
            try:
                title = clean_text(a.text)
                href = a.get_attribute("href") or ""
                if not title or not href:
                    continue
                if href in seen:
                    continue
                seen.add(href)

                # summary proche si dispo
                summary = None
                try:
                    parent = a.find_element("xpath", "./ancestor::*[self::article or contains(@class,'o-teaser')][1]")
                except Exception:
                    parent = None

                if parent:
                    for ssel in SUMMARY_SELECTORS:
                        try:
                            ps = parent.find_elements(ssel)
                        except Exception:
                            ps = []
                        found = None
                        for p in ps:
                            txt = clean_text(p.text)
                            if 20 <= len(txt) <= 400:
                                found = txt
                                break
                        if found:
                            summary = found
                            break

                items.append({
                    "title": title,
                    "url": href,
                    "summary": summary,
                    "section": base_url.replace("https://www.ft.com", "").strip("/") or "home",
                    "source": "listing",
                })
            except Exception:
                continue
    return items

def scrape_and_store_links(limit_per_section: int | None = None) -> None:
    """
    Ouvre chaque section, scrolle pour charger les teasers, extrait les liens,
    puis upsert dans MongoDB via upsert_link().
    """
    with Driver(uc=True, headless=True, locale_code="en-GB") as driver:
        driver.set_window_size(1440, 900)

        total_saved = 0
        for url in START_URLS:
            print(f"\n=== {url} ===")
            driver.get(url)

            ok = wait_for_dom_ready(driver, timeout=25)
            if not ok:
                print("[WARN] DOM pas prêt, on continue")

            click_cookie_banner_if_present(driver)
            # scroller un peu pour déclencher le lazy-load
            slow_scroll(driver, steps=10, pause=0.9)

            items = _extract_teasers_from_page(driver, url)
            if limit_per_section is not None:
                items = items[:limit_per_section]

            print(f"[INFO] {url} -> {len(items)} liens trouvés")
            saved = 0
            for it in items:
                try:
                    upsert_link({
                        "title": it["title"],
                        "url": it["url"],
                        "section": it["section"],
                        "source": it.get("source", "listing"),
                    })
                    saved += 1
                except Exception as e:
                    print("[WARN] upsert_link:", e)
            total_saved += saved
            print(f"[OK] {saved} liens upsertés pour {url}")

        print(f"\n✅ Terminé. Total liens upsertés: {total_saved}")

if __name__ == "__main__":
    # petit run de test: limite quelques liens par section pour valider
    scrape_and_store_links(limit_per_section=30)
