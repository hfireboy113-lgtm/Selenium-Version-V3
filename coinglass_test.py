import json
import re
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

URL = "https://www.coinglass.com/"
RANK_RE = re.compile(r"^\d{1,5}$")
SYMBOL_RE = re.compile(r"^[A-Za-z][A-Za-z0-9._-]{1,19}$")


def snapshot(driver, name):
    Path(f"{name}.html").write_text(driver.page_source, encoding="utf-8")
    driver.save_screenshot(f"{name}.png")


def clean(value):
    return re.sub(r"\s+", " ", value.strip())


def extract_ranked_coins(driver):
    results = []
    seen = set()
    for symbol_element in driver.find_elements(By.CSS_SELECTOR, "div.symbol-name"):
        try:
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
    return sorted(results, key=lambda item: item[0])


def wait_for_rows(driver):
    WebDriverWait(driver, 45).until(lambda d: len(extract_ranked_coins(d)) >= 3)


def click_page_number(driver, page_number):
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


def click_next(driver):
    selectors = [
        "li.ant-pagination-next",
        "li.rc-pagination-next",
        "li[title='Next Page']",
    ]
    for selector in selectors:
        for el in driver.find_elements(By.CSS_SELECTOR, selector):
            try:
                if not el.is_displayed():
                    continue
                classes = el.get_attribute("class") or ""
                if "disabled" in classes.split() or (el.get_attribute("aria-disabled") or "") == "true":
                    continue
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                driver.execute_script("arguments[0].click();", el)
                return True
            except Exception:
                pass
    return False


def wait_for_page_change(driver, old_first):
    WebDriverWait(driver, 45).until(
        lambda d: (current := extract_ranked_coins(d)) and current[0] != old_first
    )


def main():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=options)

    all_coins = []
    page_records = []
    seen_symbols = set()
    previous_last_rank = None

    try:
        print("OPENING CoinGlass...")
        driver.get(URL)
        WebDriverWait(driver, 45).until(lambda d: d.execute_script("return document.readyState") == "complete")
        wait_for_rows(driver)

        page_number = 1
        while True:
            page = extract_ranked_coins(driver)
            if len(page) < 3:
                snapshot(driver, f"coinglass_page_{page_number}_debug")
                raise RuntimeError(f"CoinGlass page {page_number}: only {len(page)} valid Rank + Coin rows detected")

            expected_first = 1 if page_number == 1 else previous_last_rank + 1
            if page[0][0] != expected_first:
                snapshot(driver, f"coinglass_page_{page_number}_rank_debug")
                raise RuntimeError(f"CoinGlass page {page_number}: expected first rank {expected_first}, found {page[0][0]}")

            print(f"PAGE {page_number}: {len(page)} coins (ranks {page[0][0]}-{page[-1][0]})")
            page_records.append({"page": page_number,"count": len(page),"first_rank": page[0][0],"last_rank": page[-1][0],"coins":[{"rank":r,"symbol":s} for r,s in page]})
            for rank, symbol in page:
                if symbol not in seen_symbols:
                    seen_symbols.add(symbol)
                    all_coins.append({"rank": rank, "symbol": symbol})

            previous_last_rank = page[-1][0]
            old_first = page[0]
            target_page = page_number + 1
            clicked = click_page_number(driver, target_page)
            if not clicked:
                clicked = click_next(driver)
            if not clicked:
                break
            try:
                wait_for_page_change(driver, old_first)
            except Exception:
                snapshot(driver, f"coinglass_page_{target_page}_change_debug")
                raise RuntimeError(f"Pagination clicked after page {page_number}, but ranked rows did not change")
            page_number += 1
            if page_number > 1000:
                raise RuntimeError("Aborted: pagination exceeded 1000 pages")

        output = {"source":"CoinGlass","url":URL,"total_coins":len(all_coins),"total_pages":len(page_records),"coins":all_coins,"pages":page_records}
        Path("coinglass_coins.json").write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        print("\nCOINGLASS TOTAL:", len(all_coins))
        print("COINGLASS PAGES:", len(page_records))
        print("OUTPUT: coinglass_coins.json")
        print("TEST_STATUS=SUCCESS")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
