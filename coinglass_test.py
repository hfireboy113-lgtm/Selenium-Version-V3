import time
import re
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

URL = "https://www.coinglass.com/"
PAGES_TO_TEST = 2
COINS_PER_PAGE = 3
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def snapshot(driver):
    Path("coinglass_debug.html").write_text(driver.page_source, encoding="utf-8")
    driver.save_screenshot("coinglass_debug.png")
    print("DEBUG_URL=", driver.current_url)
    print("DEBUG_TITLE=", driver.title)
    print("DEBUG_BODY_START=")
    print(driver.find_element(By.TAG_NAME, "body").text[:5000])


def extract_coin_names(driver):
    # First inspect all visible rows, because CoinGlass may render the grid without native table tags.
    selectors = [
        "table tbody tr",
        "[role='row']",
        "div[class*='table'] [class*='row']",
        "div[class*='Table'] [class*='row']",
    ]
    for selector in selectors:
        rows = driver.find_elements(By.CSS_SELECTOR, selector)
        values = []
        for row in rows:
            if not row.is_displayed():
                continue
            text = row.text.strip()
            if not text:
                continue
            lines = [x.strip() for x in text.splitlines() if x.strip()]
            for value in lines[:3]:
                if value and not DATE_RE.match(value) and len(value) <= 30:
                    if re.fullmatch(r"[A-Za-z0-9._-]{2,20}", value) and value not in values:
                        values.append(value)
                        break
        if values:
            return values
    return []


def main():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 30)
    try:
        print("OPENING CoinGlass...")
        driver.get(URL)
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        time.sleep(8)

        values = extract_coin_names(driver)
        if not values:
            print("Coin/Symbol rows not detected; collecting diagnostic artifacts...")
            snapshot(driver)
            raise RuntimeError("CoinGlass table was not detected; diagnostic artifacts were generated")

        print(f"PAGE 1 - FIRST {COINS_PER_PAGE} COINS:")
        for i, value in enumerate(values[:COINS_PER_PAGE], 1):
            print(f"{i}. {value}")

        # Diagnostic first: report all candidate pagination controls and attributes.
        controls = driver.find_elements(By.CSS_SELECTOR, "button, a")
        print("PAGINATION_CANDIDATES=")
        for el in controls:
            try:
                txt = (el.text or "").strip()
                aria = el.get_attribute("aria-label") or ""
                title = el.get_attribute("title") or ""
                cls = el.get_attribute("class") or ""
                if txt in {">", "›", "»", "→"} or "next" in (txt + aria + title + cls).lower():
                    print(txt, "|", aria, "|", title, "|", cls[:200])
            except Exception:
                pass

        print("TEST_STATUS=PAGE1_DETECTED")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
