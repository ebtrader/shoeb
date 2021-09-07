#!/usr/local/bin/python3

import os
import yfinance as yf
import strategies

SYMBOL = "QQQ"
DURATION = "1y"
DATA_FILE = f"data/{SYMBOL}_{DURATION}.csv"
NUM_PERIODS = 9


def main():
    if not os.path.exists(DATA_FILE):
        df = yf.download(SYMBOL, period=DURATION)
        if not os.path.exists("data"):
            os.makedirs("data")
        df.to_csv(DATA_FILE)

    hma = strategies.WMA(NUM_PERIODS)

    with open(DATA_FILE) as fp:
        first = True
        for line in fp:
            if first:  # header row, ignore
                first = False
                continue
            tokens = line.split(",")
            date = tokens[0]
            price = float(tokens[4])
            hma.update_signal(price)
            print(f"Date:{date}, Close:{'{:.2f}'.format(price)} WMA:{'{:.2f}'.format(hma.wma)} Signal:{hma.signal}")
        fp.close()


if __name__ == "__main__":
    main()
