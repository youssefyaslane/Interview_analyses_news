from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from pymongo import ASCENDING
from time import sleep
from typing import List, Tuple, Optional

from app.Database.db import collections, upsert_article

# ------------------ Core fetch ------------------

def _fetch_one_article(driver: Driver, url: str, timeout: int = 35) -> Tuple[str, str]:
    """Ouvre l'URL, attend le titre et le corps, puis retourne (title, body_article)."""
    driver.get(url)

    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

    # --- Titre ---
    title_el = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "h1.o-topper__headline span.headline__text"))
    )
    title = title_el.text.strip()

    # --- Article complet ---
    article_el = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "article#article-body"))
    )
    paragraphs = [p.text.strip() for p in article_el.find_elements(By.CSS_SELECTOR, "p") if p.text.strip()]
    body_article = "\n\n".join(paragraphs).strip()

    return title, body_article

# ------------------ Batch depuis Mongo ------------------

def _pick_urls_from_mongo(limit: Optional[int] = None) -> List[str]:
    """Sélectionne des URLs (ft_links) non encore présentes dans ft_articles. Si limit=None => toutes."""
    links, articles, _ = collections()
    existing = {a["url"] for a in articles.find({}, {"url": 1})}

    cursor = links.find(
        {"url": {"$regex": r"^https://www\.ft\.com/content/"}},
        projection={"url": 1},
        sort=[("first_seen", ASCENDING)]
    )

    out: List[str] = []
    for doc in cursor:
        url = doc["url"]
        if url not in existing:
            out.append(url)
            if isinstance(limit, int) and limit > 0 and len(out) >= limit:
                break
    return out

def fetch_articles_from_mongo(limit_per_run: Optional[int] = None,
                              headless: bool = True,
                              profile_dir: Optional[str] = None):
    """
    Parcourt les URLs à traiter depuis ft_links,
    extrait title + body_article et upsert dans ft_articles.
    limit_per_run=None => traite tout.
    """
    urls = _pick_urls_from_mongo(limit=limit_per_run)
    if not urls:
        print("[INFO] Aucune nouvelle URL à traiter.")
        return

    print(f"[INFO] {len(urls)} URL(s) à traiter.")

    driver_args = dict(
        uc=True,
        undetectable=True,
        headless=headless,
        page_load_strategy="eager",
        locale_code="en-GB",
    )
    if profile_dir:
        driver_args["user_data_dir"] = profile_dir

    total_ok = total_err = 0

    with Driver(**driver_args) as driver:
        driver.set_window_size(1440, 900)

        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] {url}")
            try:
                title, body_article = _fetch_one_article(driver, url, timeout=40)

                upsert_article({
                    "url": url,
                    "title": title,
                    "body_article": body_article,   # texte intégral
                })
                print(f"  -> ok | title: {title[:80]} | longueur body: {len(body_article)} caractères")
                total_ok += 1
            except Exception as e:
                upsert_article({
                    "url": url,
                    "title": "",
                    "body_article": "",
                })
                print(f"  -> ERROR: {type(e).__name__}: {e}")
                total_err += 1

            sleep(1.0)  # pacing

    print(f"\n✅ Terminé. {total_ok} OK, {total_err} erreurs.")

if __name__ == "__main__":
    profile_dir = r"C:\Users\HP\AppData\Local\Google\Chrome\User Data\Default"
    # None => pas de limite : traite toutes les URLs non encore présentes dans ft_articles
    fetch_articles_from_mongo(limit_per_run=None, headless=True, profile_dir=profile_dir)
