import sqlite3


class Database:

    def __init__(self, db_name="crypto_metrics.db"):
        self.conn = sqlite3.connect(db_name)

        self.create_table()


    def create_table(self):

        query = """
        CREATE TABLE IF NOT EXISTS coins (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            coin TEXT,
            price TEXT,
            mkt_cap TEXT,
            vol_24h TEXT,
            open_interest TEXT,

            oi_chg_24h TEXT,

            oi_mktcap TEXT,
            vol_mktcap TEXT,

            fr_avg TEXT,

            ls_ratio_1h TEXT,
            ls_ratio_1d TEXT,

            btc_corr_30d TEXT,
            btc_corr_7d TEXT,

            coin_link TEXT

        )
        """

        self.conn.execute(query)
        self.conn.commit()



    def save_rows(self, rows):

        query = """

        INSERT INTO coins (

            coin,
            price,
            mkt_cap,
            vol_24h,
            open_interest,
            oi_chg_24h,
            oi_mktcap,
            vol_mktcap,
            fr_avg,
            ls_ratio_1h,
            ls_ratio_1d,
            btc_corr_30d,
            btc_corr_7d,
            coin_link

        )

        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)

        """


        data = []

        for row in rows:

            data.append((

                row["coin"],
                row["price"],
                row["mkt_cap"],
                row["vol_24h"],
                row["open_interest"],

                row["oi_chg_24h"],

                row["oi_mktcap"],
                row["vol_mktcap"],

                row["fr_avg"],

                row["ls_ratio_1h"],
                row["ls_ratio_1d"],

                row["btc_corr_30d"],
                row["btc_corr_7d"],

                row["coin_link"]

            ))


        self.conn.executemany(query, data)

        self.conn.commit()



    def close(self):

        self.conn.close()