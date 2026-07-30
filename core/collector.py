from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


class CoinalyzeCollector:
    BASE_URL = "https://coinalyze.net/?columns=YSZuJmMmZCZlJnImMTUmaSYzJjYmdSZ2&order_by=price&order_dir=desc"

    def __init__(self, headless=False):
        options = Options()

        if headless:
            options.add_argument("--headless=new")

        options.add_argument("--start-maximized")

        self.driver = webdriver.Edge(
            service=Service(EdgeChromiumDriverManager().install()),
            options=options
        )

    def open(self):
        self.driver.get(self.BASE_URL)
        self.wait_table()

    def wait_table(self):
        WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "table tbody tr")
            )
        )

    def get_headers(self):
        headers = self.driver.find_elements(
            By.CSS_SELECTOR,
            "thead th"
        )

        return [header.text.strip() for header in headers]

    def get_rows(self):
        rows = self.driver.find_elements(
            By.CSS_SELECTOR,
            "tbody tr"
        )

        data = []

        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")

            if len(cells) < 14:
                continue

            coin_link = ""

            try:
                coin_link = cells[1].find_element(
                    By.TAG_NAME,
                    "a"
                ).get_attribute("href")
            except Exception:
                pass

            data.append({
                "coin": cells[1].text.strip(),
                "price": cells[2].text.strip(),
                "mkt_cap": cells[3].text.strip(),
                "vol_24h": cells[4].text.strip(),
                "open_interest": cells[5].text.strip(),
                "oi_chg_24h": cells[6].text.strip(),
                "oi_mktcap": cells[7].text.strip(),
                "vol_mktcap": cells[8].text.strip(),
                "fr_avg": cells[9].text.strip(),
                "ls_ratio_1h": cells[10].text.strip(),
                "ls_ratio_1d": cells[11].text.strip(),
                "btc_corr_30d": cells[12].text.strip(),
                "btc_corr_7d": cells[13].text.strip(),
                "coin_link": coin_link
            })
        return data
    
    def set_page(self, page):
        url = self.BASE_URL

        parsed = urlparse(url)
        query = parse_qs(parsed.query)

        query["p"] = [str(page)]

        new_query = urlencode(query, doseq=True)

        new_url = urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                parsed.fragment,
            )
        )

        print(new_url)

        self.driver.get(new_url)
        self.wait_table()

    def collect_all(self):
        all_rows = []

        page = 1

        while True:
            print(f"\n===== PAGE {page} =====")

            try:
                self.set_page(page)
            except Exception:
                print("No more pages.")
                break

            rows = self.get_rows()

            if not rows:
                print("No rows.")
                break

            print(f"Rows: {len(rows)}")

            all_rows.extend(rows)

            # آخرین صفحه
            if len(rows) < 100:
                break

            page += 1

        return all_rows

    def close(self):
        self.driver.quit()