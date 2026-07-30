class CryptoFilter:

    def __init__(self):
        pass

    def apply(self, rows):

        filtered = []

        for row in rows:

            try:
                oi_mktcap = float(row["oi_mktcap"])
                vol_mktcap = float(row["vol_mktcap"])
                ls_ratio_1d = float(row["ls_ratio_1d"])

            except:
                continue

            # قانون 1
            # VOL 24H > MKTCAP
            if vol_mktcap <= 1:
                continue

            # قانون 2
            # OI بین 10% تا 100% مارکت کپ
            if not (0.1 <= oi_mktcap <= 1):
                continue

            # قانون 3
            # Long < Short
            if ls_ratio_1d >= 1:
                continue

            filtered.append(row)

        return filtered