import time
import re
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

URL = "https://www.coinglass.com/"
COINS_PER_PAGE = 3
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def snapshot(driver, name="coinglass_debug"):
    Path(f"{name}.html").write_text(driver.page_source, encoding="utf-8")
    driver.save_screenshot(f"{name}.png")
    print("DEBUG_URL=", driver.current_url)
    print("DEBUG_TITLE=", driver.title)
    print("DEBUG_BODY_START=")
    print(driver.find_element(By.TAG_NAME, "body").text[:5000])


def extract_coin_names(driver):
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
            lines = [x.strip() for x in row.text.splitlines() if x.strip()]
            for value in lines[:4]:
                if value and not DATE_RE.match(value) and len(value) <= 30:
                    if re.fullmatch(r"[A-Za-z0-9._-]{2,20}", value) and value not in values:
                        values.append(value)
                        break
        if values:
            return values
    return []


def signature(el):
    return " | ".join([
        (el.text or "").strip(),
        el.get_attribute("aria-label") or "",
        el.get_attribute("title") or "",
        el.get_attribute("class") or "",
        el.get_attribute("data-testid") or "",
    ]).lower()


def find_next_control(driver):
    selectors = [
        "button[aria-label*='next' i]",
        "button[title*='next' i]",
        "a[aria-label*='next' i]",
        "a[title*='next' i]",
        "button[data-testid*='next' i]",
        "[role='button'][aria-label*='next' i]",
    ]
    for selector in selectors:
        for el in driver.find_elements(By.CSS_SELECTOR, selector):
            if el.is_displayed() and el.is_enabled():
                return el

    for el in driver.find_elements(By.CSS_SELECTOR, "button, a, [role='button']"):
        try:
            if not el.is_displayed() or not el.is_enabled():
                continue
            sig = signature(el)
            text = (el.text or "").strip()
            if text in {">", "›", "»", "→"} or "next page" in sig or re.search(r"\bnext\b", sig):
                return el
        except Exception:
            continue
    return None


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
            snapshot(driver)
            raise RuntimeError("CoinGlass table was not detected")

        print(f"PAGE 1 - FIRST {COINS_PER_PAGE} COINS:")
        for i, value in enumerate(values[:COINS_PER_PAGE], 1):
            print(f"{i}. {value}")

        control = find_next_control(driver)
        if control is None:
            snapshot(driver, "coinglass_pagination_debug")
            raise RuntimeError("Could not identify CoinGlass pagination control")

        print("PAGINATION_CONTROL=", signature(control)[:500])
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", control)
        driver.execute_script("arguments[0].click();", control)

        # CoinGlass keeps the same URL and may reuse the same DOM nodes. Do not wait
        # for our loose coin extractor to change; allow the client-side pagination
        # update to complete, then read the rendered rows again.
        time.sleep(5)
        values2 = extract_coin_names(driver)

        print(f"PAGE 2 - FIRST {COINS_PER_PAGE} COINS:")
        for i, value in enumerate(values2[:COINS_PER_PAGE], 1):
            print(f"{i}. {value}")

        if not values2:
            snapshot(driver, "coinglass_page2_debug")
            raise RuntimeError("Page 2 rendered, but coin rows could not be extracted")

        print("TEST_STATUS=SUCCESS")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
