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
SYMBOL_RE = re.compile(r"^[A-Za-z0-9._-]{2,20}$")


def snapshot(driver, name="coinglass_debug"):
    Path(f"{name}.html").write_text(driver.page_source, encoding="utf-8")
    driver.save_screenshot(f"{name}.png")


def clean_value(value):
    return re.sub(r"\s+", " ", value.strip())


def extract_ranked_coins(driver):
    """Extract (rank, symbol) from visible CoinGlass rows.

    We deliberately identify the ranking as a number and the coin as a
    separate non-numeric symbol, so a page-2 ranking such as 21 can never
    accidentally become the coin name.
    """
    row_selectors = [
        "table tbody tr",
        "tr",
        "[role='row']",
        "div[class*='ant-table-row']",
        "div[class*='table-row']",
        "div[class*='TableRow']",
        "div[class*='row']",
        "div[class*='Row']",
    ]

    seen = set()

    for selector in row_selectors:
        rows = driver.find_elements(By.CSS_SELECTOR, selector)
        if not rows:
            continue

        results = []
        for row in rows:
            try:
                if not row.is_displayed():
                    continue
                lines = [clean_value(x) for x in row.text.splitlines() if clean_value(x)]
                if not lines:
                    continue

                rank = None
                rank_index = None
                for i, value in enumerate(lines[:8]):
                    if re.fullmatch(r"\d{1,4}", value):
                        rank = int(value)
                        rank_index = i
                        break

                if rank is None:
                    continue

                symbol = None
                # Prefer the first valid symbol after the rank.
                for value in lines[(rank_index + 1):rank_index + 7]:
                    if DATE_RE.match(value):
                        continue
                    if value.isdigit():
                        continue
                    if SYMBOL_RE.fullmatch(value):
                        symbol = value.upper()
                        break

                if symbol is None:
                    continue

                key = (rank, symbol)
                if key not in seen:
                    seen.add(key)
                    results.append(key)
            except Exception:
                continue

        # A real table should give multiple ranked rows. Avoid returning a
        # random unrelated numbered element from the page.
        if len(results) >= COINS_PER_PAGE:
            results.sort(key=lambda item: item[0])
            return results

    return []


def click_page(driver, page_number):
    selectors = [
        f"li.rc-pagination-item-{page_number} button",
        f"li.rc-pagination-item[title='{page_number}'] button",
        f"li.rc-pagination-item-{page_number}",
    ]

    for selector in selectors:
        for el in driver.find_elements(By.CSS_SELECTOR, selector):
            try:
                if el.is_displayed() and el.is_enabled():
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
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 30)
    try:
        print("OPENING CoinGlass...")
        driver.get(URL)
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        time.sleep(8)

        page1 = extract_ranked_coins(driver)
        if not page1:
            snapshot(driver)
            raise RuntimeError("CoinGlass rows were not detected")

        print(f"PAGE 1 - FIRST {COINS_PER_PAGE} COINS:")
        for rank, symbol in page1[:COINS_PER_PAGE]:
            print(f"{rank}. {symbol}")

        if not click_page(driver, 2):
            snapshot(driver, "coinglass_pagination_debug")
            raise RuntimeError("Could not find CoinGlass page 2 control")

        time.sleep(5)
        page2 = extract_ranked_coins(driver)
        if not page2:
            snapshot(driver, "coinglass_page2_debug")
            raise RuntimeError("Page 2 selected, but ranked coin rows could not be extracted")

        print(f"PAGE 2 - FIRST {COINS_PER_PAGE} COINS:")
        for rank, symbol in page2[:COINS_PER_PAGE]:
            print(f"{rank}. {symbol}")

        print("TEST_STATUS=SUCCESS")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
