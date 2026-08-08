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


def snapshot(driver, name="coinglass_debug"):
    Path(f"{name}.html").write_text(driver.page_source, encoding="utf-8")
    driver.save_screenshot(f"{name}.png")


def clean(value):
    return re.sub(r"\s+", " ", value.strip())


def extract_ranked_coins(driver):
    """Extract Rank + Coin from the actual CoinGlass DOM structure."""
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


def click_next_page(driver):
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
                aria_disabled = el.get_attribute("aria-disabled") or ""
                if "disabled" in classes.split() or aria_disabled == "true":
                    continue

                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", el
                )
                driver.execute_script("arguments[0].click();", el)
                return True
            except Exception:
                continue

    return False


def wait_for_rank_change(driver, old_first_rank):
    def changed(d):
        current = extract_ranked_coins(d)
        return bool(current) and current[0][0] != old_first_rank

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

    all_coins = []
    page_records = []
    seen_ranks = set()

    try:
        print("OPENING CoinGlass...")
        driver.get(URL)
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        time.sleep(8)

        page_number = 1
        while True:
            page = extract_ranked_coins(driver)
            if not page:
                snapshot(driver, f"coinglass_page_{page_number}_debug")
                raise RuntimeError(
                    f"CoinGlass page {page_number}: no valid Rank + Coin rows detected"
                )

            # A page must contain a contiguous ranking starting at the expected rank.
            expected_min_rank = 1 if page_number == 1 else previous_last_rank + 1
            if page[0][0] != expected_min_rank:
                snapshot(driver, f"coinglass_page_{page_number}_rank_debug")
                raise RuntimeError(
                    f"CoinGlass page {page_number}: expected first rank {expected_min_rank}, "
                    f"found {page[0][0]}"
                )

            for rank, symbol in page:
                if rank in seen_ranks:
                    continue
                seen_ranks.add(rank)
                all_coins.append({"rank": rank, "symbol": symbol})

            page_records.append(
                {
                    "page": page_number,
                    "count": len(page),
                    "first_rank": page[0][0],
                    "last_rank": page[-1][0],
                    "coins": [
                        {"rank": rank, "symbol": symbol} for rank, symbol in page
                    ],
                }
            )

            print(
                f"PAGE {page_number}: {len(page)} coins "
                f"(ranks {page[0][0]}-{page[-1][0]})"
            )

            previous_last_rank = page[-1][0]
            old_first_rank = page[0][0]

            if not click_next_page(driver):
                break

            try:
                wait_for_rank_change(driver, old_first_rank)
            except Exception:
                snapshot(driver, f"coinglass_page_{page_number + 1}_change_debug")
                raise RuntimeError(
                    f"Pagination clicked after page {page_number}, but the ranked rows did not change"
                )

            page_number += 1

            # Defensive upper bound; this should never be reached on the real table.
            if page_number > 1000:
                raise RuntimeError("Aborted: pagination exceeded 1000 pages")

        if not all_coins:
            raise RuntimeError("No CoinGlass coins were extracted")

        output = {
            "source": "CoinGlass",
            "url": URL,
            "total_coins": len(all_coins),
            "total_pages": len(page_records),
            "coins": all_coins,
            "pages": page_records,
        }
        Path("coinglass_coins.json").write_text(
            json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        print("\nCOINGLASS TOTAL:", len(all_coins))
        print("COINGLASS PAGES:", len(page_records))
        print("OUTPUT: coinglass_coins.json")
        print("TEST_STATUS=SUCCESS")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
