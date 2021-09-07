import yfinance as yf
import pandas as pd
from finta import TA

ticker = 'NQ=F'
data = yf.download(ticker, start="2020-01-01", end="2021-09-03")
df = pd.DataFrame(data)
# print(df)
df.columns= df.columns.str.lower()
# print(df)

df['simple_moving_avg'] = TA.SMA(df, 9)
print(df)



