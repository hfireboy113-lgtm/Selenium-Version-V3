import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

URL = "https://www.coinglass.com/"
PAGES_TO_TEST = 2
COINS_PER_PAGE = 3

# Common date/number patterns are deliberately rejected when choosing a coin column.
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def table_coin_candidates(driver):
    """Find visible tables whose header contains a coin/symbol-like column."""
    candidates = []
    for table in driver.find_elements(By.CSS_SELECTOR, "table"):
        try:
            if not table.is_displayed():
                continue
            headers = [x.text.strip().lower() for x in table.find_elements(By.CSS_SELECTOR, "thead th")]
            rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
            if not rows:
                continue
            coin_indexes = [i for i, h in enumerate(headers) if h in {"coin", "symbol", "name"} or "coin" in h or "symbol" in h]
            if coin_indexes:
                candidates.append((table, coin_indexes[0]))
        except Exception:
            continue
    return candidates


def extract_coin_names(driver):
    candidates = table_coin_candidates(driver)
    for table, coin_index in candidates:
        values = []
        for row in table.find_elements(By.CSS_SELECTOR, "tbody tr"):
            cells = row.find_elements(By.CSS_SELECTOR, "td")
            if len(cells) <= coin_index:
                continue
            text = cells[coin_index].text.strip()
            if text and not DATE_RE.match(text):
                # Keep the first token; CoinGlass can render logo/name pairs in one cell.
                value = text.splitlines()[0].strip()
                if value and value not in values:
                    values.append(value)
        if values:
            return values
    return []


def click_next(driver):
    """Find pagination controls using semantic attributes/classes, not only visible text."""
    selectors = [
        "button[aria-label*='next' i]",
        "button[title*='next' i]",
        "a[aria-label*='next' i]",
        "a[title*='next' i]",
        "button[class*='next' i]",
        "a[class*='next' i]",
    ]
    for selector in selectors:
        for el in driver.find_elements(By.CSS_SELECTOR, selector):
            try:
                if not el.is_displayed() or el.get_attribute("disabled") is not None:
                    continue
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                driver.execute_script("arguments[0].click();", el)
                return True
            except Exception:
                pass

    # Fallback: inspect buttons/links in the visible pagination area for a right-arrow glyph.
    for el in driver.find_elements(By.CSS_SELECTOR, "button, a"):
        try:
            if not el.is_displayed() or el.get_attribute("disabled") is not None:
                continue
            text = (el.text or "").strip().lower()
            aria = (el.get_attribute("aria-label") or "").strip().lower()
            title = (el.get_attribute("title") or "").strip().lower()
            if text in {">", "›", "»", "→"} or any(x in (text, aria, title) for x in ("next", "next page")):
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                driver.execute_script("arguments[0].click();", el)
                return True
        except Exception:
            pass
    return False


def main():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 30)

    try:
        print("OPENING CoinGlass...")
        driver.get(URL)
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        time.sleep(6)

        previous_values = None
        for page in range(1, PAGES_TO_TEST + 1):
            wait.until(lambda d: len(extract_coin_names(d)) > 0)
            time.sleep(1)
            values = extract_coin_names(driver)
            if not values:
                raise RuntimeError("Could not identify the Coin/Symbol column in the visible CoinGlass table")

            print(f"PAGE {page} - FIRST {COINS_PER_PAGE} COINS:")
            for i, value in enumerate(values[:COINS_PER_PAGE], 1):
                print(f"{i}. {value}")

            if page < PAGES_TO_TEST:
                before = tuple(values[:10])
                if not click_next(driver):
                    raise RuntimeError("Could not find the CoinGlass pagination Next control")
                wait.until(lambda d: tuple(extract_coin_names(d)[:10]) != before)

        print("TEST_STATUS=SUCCESS")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
