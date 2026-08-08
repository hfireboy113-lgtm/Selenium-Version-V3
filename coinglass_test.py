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
ROWS_PER_PAGE = 100


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
    WebDriverWait(driver, 60).until(lambda d: len(extract_ranked_coins(d)) >= 3)


def set_page_size_100(driver):
    """Try to select 100 rows/page from Ant Design's page-size selector."""
    selectors = [
        ".ant-pagination-options-size-changer",
        "div.ant-select[aria-label*='page' i]",
        ".ant-pagination .ant-select",
    ]
    for selector in selectors:
        for el in driver.find_elements(By.CSS_SELECTOR, selector):
            try:
                if not el.is_displayed():
                    continue
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                driver.execute_script("arguments[0].click();", el)
                time.sleep(0.5)
                # Ant Design renders options in a portal outside the selector.
                options = driver.find_elements(By.CSS_SELECTOR, ".ant-select-item-option")
                for option in options:
                    if clean(option.text) == "100" and option.is_displayed():
                        driver.execute_script("arguments[0].click();", option)
                        WebDriverWait(driver, 30).until(
                            lambda d: len(extract_ranked_coins(d)) >= 3
                        )
                        print("PAGE SIZE: 100")
                        return True
                # Some versions use native-looking option elements.
                for option in driver.find_elements(By.XPATH, "//*[normalize-space(text())='100']"):
                    try:
                        if option.is_displayed() and option.is_enabled():
                            driver.execute_script("arguments[0].click();", option)
                            WebDriverWait(driver, 30).until(lambda d: len(extract_ranked_coins(d)) >= 3)
                            print("PAGE SIZE: 100")
                            return True
                    except Exception:
                        continue
            except Exception:
                continue
    print("PAGE SIZE: 100 not changed; using current page size")
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
                continue
    return False


def wait_for_page_change(driver, old_first):
    WebDriverWait(driver, 60).until(
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
        WebDriverWait(driver, 60).until(lambda d: d.execute_script("return document.readyState") == "complete")
        wait_for_rows(driver)
        set_page_size_100(driver)

        page_number = 1
        while True:
            page = extract_ranked_coins(driver)
            if len(page) < 3:
                snapshot(driver, f"coinglass_page_{page_number}_debug")
                raise RuntimeError(f"CoinGlass page {page_number}: only {len(page)} valid Rank + Coin rows detected")

            if page_number > 1 and page[0][0] <= previous_last_rank:
                snapshot(driver, f"coinglass_page_{page_number}_rank_debug")
                raise RuntimeError(
                    f"CoinGlass page {page_number}: first rank {page[0][0]} is not after previous page last rank {previous_last_rank}"
                )

            print(f"PAGE {page_number}: {len(page)} coins (ranks {page[0][0]}-{page[-1][0]})")
            page_records.append({
                "page": page_number,
                "count": len(page),
                "first_rank": page[0][0],
                "last_rank": page[-1][0],
                "coins": [{"rank": r, "symbol": s} for r, s in page],
            })
            for rank, symbol in page:
                if symbol not in seen_symbols:
                    seen_symbols.add(symbol)
                    all_coins.append({"rank": rank, "symbol": symbol})

            previous_last_rank = page[-1][0]
            old_first = page[0]
            if not click_next(driver):
                break
            try:
                wait_for_page_change(driver, old_first)
            except Exception:
                snapshot(driver, f"coinglass_page_{page_number + 1}_change_debug")
                raise RuntimeError(f"Pagination clicked after page {page_number}, but ranked rows did not change")
            page_number += 1
            if page_number > 100:
                raise RuntimeError("Aborted: pagination exceeded 100 pages")

        output = {
            "source": "CoinGlass",
            "url": URL,
            "page_size_requested": ROWS_PER_PAGE,
            "total_coins": len(all_coins),
            "total_pages": len(page_records),
            "coins": all_coins,
            "pages": page_records,
        }
        Path("coinglass_coins.json").write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        print("\nCOINGLASS TOTAL:", len(all_coins))
        print("COINGLASS PAGES:", len(page_records))
        print("OUTPUT: coinglass_coins.json")
        print("TEST_STATUS=SUCCESS")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
