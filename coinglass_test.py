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


def clean_value(value):
    return re.sub(r"\s+", " ", value.strip())


def extract_coin_rows(driver):
    """Extract (rank, coin) from the Coin/Symbol column, not by row order."""
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

            header_selectors = [
                "thead tr th",
                "[role='columnheader']",
                "thead th",
            ]
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

            row_selectors = [
                "tbody tr",
                "[role='row']",
            ]
            rows = []
            for selector in row_selectors:
                rows = [r for r in table.find_elements(By.CSS_SELECTOR, selector) if r.is_displayed()]
                if rows:
                    break

            values = []
            for row in rows:
                cells = [
                    clean_value(x.text)
                    for x in row.find_elements(By.CSS_SELECTOR, "td, [role='cell']")
                ]
                cells = [x for x in cells if x]
                if coin_index < len(cells):
                    value = cells[coin_index]
                    if value and not value.isdigit() and re.fullmatch(r"[A-Za-z0-9._-]{2,20}", value):
                        if value not in [coin for _, coin in values]:
                            rank = cells[0] if cells and cells[0].isdigit() else "?"
                            values.append((rank, value))

            if values:
                return values

    # Fallback for layouts where headers are not exposed semantically.
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
            lines = [clean_value(x) for x in row.text.splitlines() if clean_value(x)]
            if not lines:
                continue

            rank = lines[0] if lines[0].isdigit() else "?"
            for value in lines[1:7]:
                if (
                    value
                    and not DATE_RE.match(value)
                    and not value.isdigit()
                    and len(value) <= 30
                    and re.fullmatch(r"[A-Za-z0-9._-]{2,20}", value)
                ):
                    if value not in [coin for _, coin in values]:
                        values.append((rank, value))
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

        page1 = extract_coin_rows(driver)
        if not page1:
            snapshot(driver)
            raise RuntimeError("CoinGlass table was not detected")

        print(f"PAGE 1 - FIRST {COINS_PER_PAGE} COINS:")
        for rank, value in page1[:COINS_PER_PAGE]:
            print(f"{rank}. {value}")

        page2_selectors = [
            "li.rc-pagination-item-2 button",
            "li.rc-pagination-item[title='2'] button",
            "li.rc-pagination-item-2",
        ]
        clicked = False
        for selector in page2_selectors:
            for el in driver.find_elements(By.CSS_SELECTOR, selector):
                try:
                    if el.is_displayed() and el.is_enabled():
                        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                        driver.execute_script("arguments[0].click();", el)
                        clicked = True
                        break
                except Exception:
                    pass
            if clicked:
                break

        if not clicked:
            snapshot(driver, "coinglass_pagination_debug")
            raise RuntimeError("Could not find CoinGlass page 2 control")

        time.sleep(5)
        page2 = extract_coin_rows(driver)
        if not page2:
            snapshot(driver, "coinglass_page2_debug")
            raise RuntimeError("Page 2 selected, but coin rows could not be extracted")

        print(f"PAGE 2 - FIRST {COINS_PER_PAGE} COINS:")
        for rank, value in page2[:COINS_PER_PAGE]:
            print(f"{rank}. {value}")

        print("TEST_STATUS=SUCCESS")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
