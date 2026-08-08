import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL = "https://www.coinglass.com/"
PAGES_TO_TEST = 2
COINS_PER_PAGE = 3


def visible_texts(driver):
    # Prefer table rows/cells; fall back to links that look like coin rows.
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    result = []
    for row in rows:
        cells = row.find_elements(By.CSS_SELECTOR, "td")
        if cells:
            text = cells[0].text.strip()
            if text:
                result.append(text)
    if result:
        return result

    links = driver.find_elements(By.CSS_SELECTOR, "a")
    for link in links:
        text = link.text.strip()
        if text and len(text) <= 20:
            result.append(text)
    return result


def click_next(driver):
    candidates = driver.find_elements(By.XPATH, "//button | //a")
    for el in candidates:
        try:
            label = (el.text or "").strip().lower()
            aria = (el.get_attribute("aria-label") or "").strip().lower()
            title = (el.get_attribute("title") or "").strip().lower()
            disabled = el.get_attribute("disabled") is not None
            if disabled:
                continue
            if label in {"next", ">", "›", "→"} or "next" in aria or "next" in title:
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
        time.sleep(5)

        previous = None
        for page in range(1, PAGES_TO_TEST + 1):
            wait.until(lambda d: len(visible_texts(d)) > 0)
            time.sleep(2)
            values = visible_texts(driver)
            print(f"PAGE {page} - FIRST {COINS_PER_PAGE} ROWS:")
            for i, value in enumerate(values[:COINS_PER_PAGE], 1):
                print(f"{i}. {value}")

            if page < PAGES_TO_TEST:
                before = driver.current_url + "|" + "|".join(values[:10])
                if not click_next(driver):
                    raise RuntimeError("Could not find the Next pagination control")
                wait.until(lambda d: (d.current_url + "|" + "|".join(visible_texts(d)[:10])) != before)

        print("TEST_STATUS=SUCCESS")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
