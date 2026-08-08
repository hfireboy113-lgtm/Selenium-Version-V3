import time
import re
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

URL = "https://www.coinglass.com/"
COINS_PER_PAGE = 3
RANK_RE = re.compile(r"^\d{1,5}$")
SYMBOL_RE = re.compile(r"^[A-Za-z][A-Za-z0-9._-]{1,19}$")


def snapshot(driver, name="coinglass_debug"):
    Path(f"{name}.html").write_text(driver.page_source, encoding="utf-8")
    driver.save_screenshot(f"{name}.png")


def clean(value):
    return re.sub(r"\s+", " ", value.strip())


def extract_ranked_coins(driver):
    """Extract Rank + Coin from the actual CoinGlass DOM structure.

    CoinGlass exposes the coin as div.symbol-name inside its Coin <td>.
    The Rank is the immediately preceding <td> in the same table row.
    """
    symbol_elements = driver.find_elements(By.CSS_SELECTOR, "div.symbol-name")
    results = []
    seen = set()

    for symbol_element in symbol_elements:
        try:
            if not symbol_element.is_displayed():
                continue

            symbol = clean(symbol_element.text).upper()
            if not SYMBOL_RE.fullmatch(symbol):
                continue

            coin_td = symbol_element.find_element(By.XPATH, "ancestor::td[1]")
            preceding = coin_td.find_elements(By.XPATH, "preceding-sibling::td[1]")
            if not preceding:
                continue

            rank_text = clean(preceding[0].text)
            if not RANK_RE.fullmatch(rank_text):
                continue

            rank = int(rank_text)
            if rank <= 0:
                continue

            # Validate against CoinGlass's own /currencies/SYMBOL link.
            links = coin_td.find_elements(By.CSS_SELECTOR, "a[href*='/currencies/']")
            if links:
                href = links[0].get_attribute("href") or ""
                href_symbol = href.rstrip("/").split("/currencies/")[-1].split("?")[0]
                if href_symbol and href_symbol.upper() != symbol:
                    continue

            item = (rank, symbol)
            if item not in seen:
                seen.add(item)
                results.append(item)
        except Exception:
            continue

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


def wait_for_page_change(driver, old_first):
    def changed(d):
        current = extract_ranked_coins(d)
        return bool(current) and current[0] != old_first

    WebDriverWait(driver, 30).until(changed)


def main():
    options = webdriver.ChromeOptions()
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
            snapshot(driver, "coinglass_page1_debug")
            raise RuntimeError(
                f"CoinGlass ranked rows not detected: found {len(page1)} valid rows"
            )

        print(f"PAGE 1 - FIRST {COINS_PER_PAGE} COINS:")
        for rank, symbol in page1[:COINS_PER_PAGE]:
            print(f"{rank}. {symbol}")

        old_first = page1[0]
        if not click_page(driver, 2):
            snapshot(driver, "coinglass_pagination_debug")
            raise RuntimeError("Could not find CoinGlass page 2 control")

        wait_for_page_change(driver, old_first)

        page2 = extract_ranked_coins(driver)
        if len(page2) < COINS_PER_PAGE:
            snapshot(driver, "coinglass_page2_debug")
            raise RuntimeError(
                f"Page 2 selected, but only {len(page2)} valid ranked rows were extracted"
            )

        print(f"PAGE 2 - FIRST {COINS_PER_PAGE} COINS:")
        for rank, symbol in page2[:COINS_PER_PAGE]:
            print(f"{rank}. {symbol}")

        if page2[0][0] <= page1[-1][0]:
            snapshot(driver, "coinglass_rank_validation_debug")
            raise RuntimeError(
                f"Page 2 rank validation failed: page1 ends at {page1[-1][0]}, "
                f"page2 starts at {page2[0][0]}"
            )

        print("TEST_STATUS=SUCCESS")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
