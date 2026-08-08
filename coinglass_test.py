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
    """Extract (rank, symbol) using the actual CoinGlass table columns."""
    table_selectors = [
        "table",
        "[role='table']",
        "div[class*='table']",
        "div[class*='Table']",
    ]

    for table_selector in table_selectors:
        tables = driver.find_elements(By.CSS_SELECTOR, table_selector)
        for table in tables:
            if not table.is_displayed():
                continue

            header_selectors = ["thead tr th", "[role='columnheader']", "thead th"]
            headers = []
            for selector in header_selectors:
                headers = [
                    clean_value(x.text)
                    for x in table.find_elements(By.CSS_SELECTOR, selector)
                    if x.is_displayed() and clean_value(x.text)
                ]
                if headers:
                    break

            coin_index = None
            for i, header in enumerate(headers):
                normalized = re.sub(r"[^a-z]", "", header.lower())
                if normalized in {"coin", "symbol", "coinsymbol", "coinname"}:
                    coin_index = i
                    break

            if coin_index is None:
                continue

            row_selectors = ["tbody tr", "[role='row']"]
            rows = []
            for selector in row_selectors:
                rows = [
                    r for r in table.find_elements(By.CSS_SELECTOR, selector)
                    if r.is_displayed()
                ]
                if rows:
                    break

            results = []
            for row in rows:
                cells = [
                    clean_value(x.text)
                    for x in row.find_elements(By.CSS_SELECTOR, "td, [role='cell']")
                ]
                cells = [x for x in cells if x]

                if coin_index >= len(cells):
                    continue

                symbol = cells[coin_index]
                if not SYMBOL_RE.fullmatch(symbol) or symbol.isdigit():
                    continue

                # In the CoinGlass table the Rank column is immediately
                # before the Coin column. Read that exact cell instead of
                # using the position in our extracted Python list.
                rank = None
                if coin_index > 0 and re.fullmatch(r"\d{1,4}", cells[coin_index - 1]):
                    rank = int(cells[coin_index - 1])

                if rank is None:
                    # Some layouts expose the rank as the first cell.
                    for candidate in cells[:coin_index]:
                        if re.fullmatch(r"\d{1,4}", candidate):
                            rank = int(candidate)
                            break

                if rank is None:
                    continue

                item = (rank, symbol.upper())
                if item not in results:
                    results.append(item)

            if len(results) >= COINS_PER_PAGE:
                results.sort(key=lambda item: item[0])
                return results

    # Do not guess from arbitrary page text. If the table/header structure
    # changes, fail loudly so a bad metric can never be reported as a coin.
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
                    driver.execute_script(
                        "arguments[0].scrollIntoView({block:'center'});", el
                    )
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
            raise RuntimeError("CoinGlass table was not detected")

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
            raise RuntimeError(
                "Page 2 selected, but ranked coin rows could not be extracted"
            )

        print(f"PAGE 2 - FIRST {COINS_PER_PAGE} COINS:")
        for rank, symbol in page2[:COINS_PER_PAGE]:
            print(f"{rank}. {symbol}")

        print("TEST_STATUS=SUCCESS")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
