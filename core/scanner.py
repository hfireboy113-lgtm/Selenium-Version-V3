from core.collector import CoinalyzeCollector
from core.database import Database
from core.filters import CryptoFilter
from core.formatter import Formatter


class Scanner:


    def __init__(self):

        self.collector = CoinalyzeCollector()

        self.database = Database()

        self.crypto_filter = CryptoFilter()

        self.formatter = Formatter()



    def run(self):

        # دریافت اطلاعات از Coinalyze

        self.collector.open()

        rows = self.collector.collect_all()


        print()
        print("=" * 50)
        print(f"TOTAL COINS : {len(rows)}")
        print("=" * 50)



        # ذخیره دیتابیس

        self.database.save_rows(rows)



        # فیلتر WatchList

        watchlist = self.crypto_filter.apply(rows)


        print()
        print("=" * 50)
        print(f"FILTERED COINS : {len(watchlist)}")
        print("=" * 50)



        # ساخت خروجی

        output = self.formatter.format_watchlist(watchlist)


        return output



    def close(self):

        self.database.close()

        self.collector.close()