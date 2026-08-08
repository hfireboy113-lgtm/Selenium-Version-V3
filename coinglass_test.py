import time
import re
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

URL = "https://www.coinglass.com/"
COINS_PER_PAGE = 3
RANK_RE = re.compile(r"^\d{1,4}$")
SYMBOL_RE = re.compile(r"^[A-Za-z0-9._-]{2,20}$")


def snapshot(driver, name="coinglass_debug"):
    Path(f"{name}.html").write_text(driver.page_source, encoding="utf-8")
    driver.save_screenshot(f"{name}.png")


def clean(value):
    return re.sub(r"\s+", " ", value.strip())


def extract_ranked_coins(driver):
    """Read Rank and Coin directly from the CoinGlass row/cell DOM."""
    rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")
    results = []

    for row in rows:
        if not row.is_displayed():
            continue

        # CoinGlass exposes the symbol in: <div class="symbol-name">BTC</div>
        symbol_elements = row.find_elements(By.CSS_SELECTOR, "div.symbol-name")
        if not symbol_elements:
            continue

        symbol = clean(symbol_elements[0].text).upper()
        if not SYMBOL_RE.fullmatch(symbol) or symbol.isdigit():
            continue

        # The first fixed-left cell is the Rank cell in the supplied CoinGlass DOM:
        # <td class="ant-table-cell ant-table-cell-fix-left"><div>1</div></td>
        rank = None
        cells = row.find_elements(By.CSS_SELECTOR, "td")
        for cell in cells:
            classes = cell.get_attribute("class") or ""
            if "ant-table-cell-fix-left" not in classes:
                continue
            text = clean(cell.text)
            if RANK_RE.fullmatch(text):
                rank = int(text)
                break

        if rank is None:
            continue

        # Independent validation: CoinGlass puts the symbol in /currencies/SYMBOL.
        links = row.find_elements(By.CSS_SELECTOR, "a[href^='/currencies/']")
        if links:
            href = links[0].get_attribute("href") or ""
            href_symbol = href.rstrip("/").split("/currencies/")[-1].upper()
            if href_symbol and href_symbol != symbol:
                continue

        item = (rank, symbol)
        if item not in results:
            results.append(item)

    results.sort(key=lambda item: item[0])
    return results


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


def wait_for_page_change(driver, old_ranks):
    def changed(d):
        current = extract_ranked_coins(d)
        current_ranks = tuple(x[0] for x in current[:COINS_PER_PAGE])
        return current_ranks and current_ranks != old_ranks

    WebDriverWait(driver, 20).until(changed)


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
        if len(page1) < COINS_PER_PAGE:
            snapshot(driver)
            raise RuntimeError(
                f"CoinGlass ranked rows not detected: found {len(page1)} valid rows"
            )

        print(f"PAGE 1 - FIRST {COINS_PER_PAGE} COINS:")
        for rank, symbol in page1[:COINS_PER_PAGE]:
            print(f"{rank}. {symbol}")

        old_ranks = tuple(x[0] for x in page1[:COINS_PER_PAGE])

        if not click_page(driver, 2):
            snapshot(driver, "coinglass_pagination_debug")
            raise RuntimeError("Could not find CoinGlass page 2 control")

        wait_for_page_change(driver, old_ranks)
        time.sleep(1)

        page2 = extract_ranked_coins(driver)
        if len(page2) < COINS_PER_PAGE:
            snapshot(driver, "coinglass_page2_debug")
            raise RuntimeError(
                f"Page 2 selected, but only {len(page2)} valid ranked rows were extracted"
            )

        new_ranks = tuple(x[0] for x in page2[:COINS_PER_PAGE])
        if new_ranks == old_ranks:
            snapshot(driver, "coinglass_page2_unchanged_debug")
            raise RuntimeError("Page 2 did not produce a different ranked row set")

        print(f"PAGE 2 - FIRST {COINS_PER_PAGE} COINS:")
        for rank, symbol in page2[:COINS_PER_PAGE]:
            print(f"{rank}. {symbol}")

        print("TEST_STATUS=SUCCESS")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
