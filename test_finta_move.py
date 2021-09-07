import yfinance as yf
import pandas as pd
# from finta import TA

ticker = 'NQ=F'
data = yf.download(ticker, start="2020-01-01", end="2021-09-03")
df = pd.DataFrame(data)
# print(df)
df.columns= df.columns.str.lower()
# print(df)

def SMA(ohlc = df, period: int = 41, column: str = "close"):
    """
    Simple moving average - rolling mean in pandas lingo. Also known as 'MA'.
    The simple moving average (SMA) is the most basic of the moving averages used for trading.
    """

    return pd.Series(
        ohlc[column].rolling(window=period).mean(),
        name="{0} period SMA".format(period),
    )

df['simple_moving_avg'] = SMA(df)
print(df)
# df['hma'] = TA.HMA(df, 9)
# print(df)




