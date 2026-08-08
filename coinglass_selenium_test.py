from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

URL = "https://www.coinglass.com/"


def get_coin_names(driver):
    # CoinGlass is a React/Next-style dynamic page, so inspect visible table rows
    # rather than relying on a single brittle CSS selector.
    candidates = driver.find_elements(By.CSS_SELECTOR, "tr")
    names = []
    for row in candidates:
        try:
            cells = row.find_elements(By.CSS_SELECTOR, "td")
            if not cells:
                continue
            texts = [c.text.strip() for c in cells]
            if texts and texts[0] and texts[0].lower() not in {"coin", "name"}:
                names.append(texts[0])
        except Exception:
            continue
    return names


def click_next(driver):
    selectors = [
        "button[aria-label*='Next' i]",
        "button[title*='Next' i]",
        "a[aria-label*='Next' i]",
        "a[title*='Next' i]",
        "button",
        "a",
    ]
    for selector in selectors:
        for element in driver.find_elements(By.CSS_SELECTOR, selector):
            try:
                text = (element.text or "").strip().lower()
                aria = (element.get_attribute("aria-label") or "").lower()
                title = (element.get_attribute("title") or "").lower()
                if "next" in text or "next" in aria or "next" in title or text in {">", "›", "»"}:
                    if element.is_displayed() and element.is_enabled():
                        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
                        driver.execute_script("arguments[0].click();", element)
                        return True
            except Exception:
                continue
    return False


def main():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(URL)
        WebDriverWait(driver, 30).until(lambda d: d.execute_script("return document.readyState") == "complete")
        time.sleep(8)

        for page in (1, 2):
            names = get_coin_names(driver)
            print(f"PAGE {page} FIRST 3 COINS: {names[:3]}")
            if page == 2:
                break
            if not click_next(driver):
                print("Could not find a usable Next control. Dumping visible pagination text:")
                for el in driver.find_elements(By.CSS_SELECTOR, "button, a"):
                    try:
                        txt = (el.text or "").strip()
                        if txt:
                            print(repr(txt))
                    except Exception:
                        pass
                raise RuntimeError("Could not find the Next pagination control")
            time.sleep(3)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
