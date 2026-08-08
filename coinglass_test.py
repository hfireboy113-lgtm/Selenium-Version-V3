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


def extract_coin_names(driver):
    selectors = ["table tbody tr", "[role='row']", "div[class*='table'] [class*='row']", "div[class*='Table'] [class*='row']"]
    for selector in selectors:
        rows = driver.find_elements(By.CSS_SELECTOR, selector)
        values = []
        for row in rows:
            if not row.is_displayed():
                continue
            lines = [x.strip() for x in row.text.splitlines() if x.strip()]
            for value in lines[:4]:
                if value and not DATE_RE.match(value) and len(value) <= 30 and re.fullmatch(r"[A-Za-z0-9._-]{2,20}", value):
                    if value not in values:
                        values.append(value)
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

        page1 = extract_coin_names(driver)
        if not page1:
            snapshot(driver)
            raise RuntimeError("CoinGlass table was not detected")

        print(f"PAGE 1 - FIRST {COINS_PER_PAGE} COINS:")
        for i, value in enumerate(page1[:COINS_PER_PAGE], 1):
            print(f"{i}. {value}")

        # CoinGlass pagination is rc-pagination. Page 2 is rendered as:
        # <li title="2" class="rc-pagination-item rc-pagination-item-2"><button>2</button></li>
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
        page2 = extract_coin_names(driver)
        if not page2:
            snapshot(driver, "coinglass_page2_debug")
            raise RuntimeError("Page 2 selected, but coin rows could not be extracted")

        print(f"PAGE 2 - FIRST {COINS_PER_PAGE} COINS:")
        for i, value in enumerate(page2[:COINS_PER_PAGE], 1):
            print(f"{i}. {value}")

        print("TEST_STATUS=SUCCESS")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
