import numpy as np
from finta import TA
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px


import pandas as pd

from datetime import timedelta

""" do WMA 9 (all ATR w/i 1 band) 21 or 34 (smooth trend) for daily or 9 for weekly n = 5 ATR = 21"""
""" do change period 45 or 15 or 6 on weeklies - go back to the place of trend change"""
""" WMA9 for 2 day bars with ATR 21 """

ticker = "ES=F"

# data = yf.download(tickers = ticker, start='2019-01-04', end='2021-06-09')
data = yf.download(tickers = ticker, period = "2y", interval = '1wk')

# valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
# valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
# data = yf.download("SPY AAPL", start="2017-01-01", end="2017-04-30")

df = pd.DataFrame(data)

df = df.reset_index()

# print(df)

df['WMA'] = TA.WMA(df, 9)

# print(df)

# Calculate the difference between rows

# https://www.codeforests.com/2020/10/04/calculate-date-difference-between-rows/

df['WMA_diff'] = df['WMA'].diff()

# print(df)

# https://stackoverflow.com/questions/32984462/setting-1-or-0-to-new-pandas-column-conditionally
# 1 or 0 switch

df['slope'] = df['WMA_diff'] > 0

# print(df)

df['slope'] = df['slope'].astype(int)

# print(df)

# https://newbedev.com/comparing-previous-row-values-in-pandas-dataframe

df['trigger'] = df['slope'].eq(df['slope'].shift())

df['trigger'] = df['trigger'].astype(int)

df['buy'] = (df['trigger'] == 0) & (df['slope'] > 0)

df['buy'] = df['buy'].astype(int)

# df['rolling_min'] = df['Low'].rolling(window=3).min().shift(1).fillna(0)

df['rolling_min'] = df['Low'].rolling(window=4).min().fillna(0)

df['vertex'] = np.where(df['buy'], df['rolling_min'], 0)

df['sell'] = (df['trigger'] == 0) & (df['slope'] == 0)

df['sell'] = df['sell'].astype(int)

# df['rolling_max'] = df['High'].rolling(window=3).max().shift(1).fillna(0)

df['rolling_max'] = df['High'].rolling(window=4).max().fillna(0)

df['neckline'] = np.where(df['sell'], df['rolling_max'], 0)

# convert neckline to list

neck_list = df['neckline'].tolist()

neck_list = [i for i in neck_list if i != 0]

print(neck_list)

df['Date'] = df['Date'].astype(str)

df['neck_date'] = np.where(df['neckline'], df['Date'], 0)

neck_date_list = df['neck_date'].tolist()

neck_date_list = [i for i in neck_date_list if i != 0]

print(neck_date_list)

# convert 2 columns into a dictionary

# https://cmdlinetips.com/2021/04/convert-two-column-values-from-pandas-dataframe-to-a-dictionary/

# https://stackoverflow.com/questions/66311549/how-do-i-loop-over-multiple-figures-in-plotly

# https://stackoverflow.com/questions/60926439/plotly-add-traces-using-a-loop

print(df)

# df.to_csv('switch.csv')

# fig = px.scatter(x=neck_date_list, y=neck_list)
# fig.show()

fig1 = go.Figure(data=[go.Candlestick(x=df['Date'],
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'])]

)

fig1.add_shape(type="rect",
    x0=neck_date_list[0], y0=neck_list[0], x1=neck_date_list[1], y1=neck_list[0],
    line=dict(
        color="LightSeaGreen",
        width=2,
    ),
   fillcolor="RoyalBlue", opacity=0.4,

)


fig1.show()
