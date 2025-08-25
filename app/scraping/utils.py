# app/utils.py
import re
import time
from typing import Optional
from seleniumbase import Driver

def clean_text(s: Optional[str]) -> str:
    """Compacte les espaces et strip."""
    if not s:
        return ""
    return re.sub(r"\s+", " ", s).strip()

def wait_for_dom_ready(driver: Driver, timeout: int = 20) -> bool:
    """Attend document.readyState === 'complete'."""
    end = time.time() + timeout
    while time.time() < end:
        try:
            if driver.execute_script("return document.readyState") == "complete":
                return True
        except Exception:
            pass
        time.sleep(0.25)
    return False

def click_cookie_banner_if_present(driver: Driver) -> None:
    """Clique un bouton d'acceptation si présent (heuristique générique)."""
    try:
        driver.execute_script("""
            const btns = Array.from(
              document.querySelectorAll('button, [role="button"], input[type="button"], input[type="submit"]')
            );
            for (const el of btns) {
              const t = (el.innerText || el.value || '').trim().toLowerCase();
              if (t.includes('accept') || t.includes('agree')) {
                try { el.click(); return; } catch(e) {}
              }
            }
        """)
        time.sleep(0.8)
    except Exception:
        pass

    # Sélecteurs additionnels
    for sel in [
        "button[title*='Accept']",
        "button[aria-label*='Accept']",
        "button[aria-label*='agree' i]",
    ]:
        try:
            if driver.is_element_visible(sel, timeout=1.5):
                driver.click(sel)
                time.sleep(0.6)
                break
        except Exception:
            continue

def slow_scroll(driver: Driver, steps: int = 10, pause: float = 0.9) -> None:
    """Scroll progressif pour déclencher lazy-load."""
    last_h = 0
    for _ in range(steps):
        try:
            driver.execute_script("window.scrollBy(0, Math.max(350, window.innerHeight));")
            time.sleep(pause)
            h = driver.execute_script("return document.body.scrollHeight || 0;")
            if h == last_h:
                break
            last_h = h
        except Exception:
            break
