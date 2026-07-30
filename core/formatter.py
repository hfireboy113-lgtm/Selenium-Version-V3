import jdatetime

from datetime import datetime
from zoneinfo import ZoneInfo


class Formatter:

    def __init__(self):
        pass

    def format_watchlist(self, watchlist):

        tehran_time = datetime.now(ZoneInfo("Asia/Tehran"))

        jalali_date = jdatetime.datetime.fromgregorian(
            datetime=tehran_time
        ).strftime("%Y/%m/%d")

        tehran_clock = tehran_time.strftime("%H:%M")

        text = ""

        text += "==========================================\n"
        text += "📊 COINALYZE WATCHLIST\n\n"

        text += f"Date  : {jalali_date}\n"
        text += f"Time  : {tehran_clock} (Tehran)\n\n"

        text += f"Coins Found : {len(watchlist)}\n"

        text += "==========================================\n\n"

        for index, coin in enumerate(watchlist, start=1):

            text += f"{index}) {coin['coin']}\n\n"

            text += f"PRICE : {coin['price']}\n\n"

            text += f"MKTCAP : {coin['mkt_cap']}\n\n"

            text += f"VOL 24H : {coin['vol_24h']}\n\n"

            text += f"OI : {coin['open_interest']}\n\n"

            # ===============================
            # VOL24H / MKTCAP
            # ===============================
            try:
                if float(coin["vol_mktcap"]) >= 1:
                    text += f"✅ VOL 24H / MKTCAP : {coin['vol_mktcap']}\n\n"
                else:
                    text += f"VOL 24H / MKTCAP : {coin['vol_mktcap']}\n\n"
            except:
                text += f"VOL 24H / MKTCAP : {coin['vol_mktcap']}\n\n"

            # ===============================
            # OI / MKTCAP
            # ===============================
            try:
                oi = float(coin["oi_mktcap"])

                if 0.1 <= oi <= 1:
                    text += f"✅ OI / MKTCAP : {coin['oi_mktcap']}\n\n"
                else:
                    text += f"OI / MKTCAP : {coin['oi_mktcap']}\n\n"
            except:
                text += f"OI / MKTCAP : {coin['oi_mktcap']}\n\n"

            # ===============================
            # L/S Ratio 1D
            # ===============================
            try:
                if float(coin["ls_ratio_1d"]) < 1:
                    text += f"✅ L/S RATIO (1D) : {coin['ls_ratio_1d']}\n\n"
                else:
                    text += f"L/S RATIO (1D) : {coin['ls_ratio_1d']}\n\n"
            except:
                text += f"L/S RATIO (1D) : {coin['ls_ratio_1d']}\n\n"

            text += f"L/S RATIO (1H) : {coin['ls_ratio_1h']}\n\n"

            text += f"FR AVG : {coin['fr_avg']}\n\n"

            text += f"OI CHG 24H % : {coin['oi_chg_24h']}\n\n"

            text += f"BTC CORR 7D : {coin['btc_corr_7d']}\n\n"

            text += f"BTC CORR 30D : {coin['btc_corr_30d']}\n\n"

            text += f"COIN LINK : {coin['coin_link']}\n"

            text += "==========================================\n\n"

        return text