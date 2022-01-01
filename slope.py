import math
import numpy as np
from finta import TA
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

ticker = "NQ=F"
data = yf.download(tickers = ticker, start='2020-01-04', end='2021-12-10')
# data = yf.download(tickers = ticker, period = "3y")

# valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
# valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo

df1 = pd.DataFrame(data)

df = df1.reset_index()

df7 = df.rename(columns = {'Date': 'date', 'Open':'open', 'High': 'high', 'Low':'low', 'Close':'close','Volume': 'volume'}, inplace = False)

# print(df7)
df7.to_csv('daily.csv')

n = 5

df3 = df7.groupby(np.arange(len(df7))//n).max() # high

df4 = df7.groupby(np.arange(len(df7))//n).min() # low

df5 = df7.groupby(np.arange(len(df7))//n).first() # open

df6 = df7.groupby(np.arange(len(df7))//n).last() # close


agg_df = pd.DataFrame()

agg_df['date'] = df6['date']
agg_df['low'] = df4['low']
agg_df['high'] = df3['high']
agg_df['open'] = df5['open']
agg_df['close'] = df6['close']

df2 = agg_df

print(df2)
num_periods = 21
df2['SMA'] = TA.SMA(df2, 21)
df2['FRAMA'] = TA.FRAMA(df2, 10)
df2['TEMA'] = TA.TEMA(df2, num_periods)
# df2['VWAP'] = TA.VWAP(df2)

# how to get previous row's value
# df2['previous'] = df2['lower_band'].shift(1)

# recursive
df2['test'] = 5
df2.loc[0, 'diff'] = df2.loc[0, 'test'] * 0.4
df2.loc[1, 'diff'] = df2.loc[1, 'test'] * 0.4
df2.loc[2, 'diff'] = df2.loc[2, 'test'] * 0.4
df2.loc[3, 'diff'] = df2.loc[3, 'test'] * 0.4

for i in range(4, len(df2)):
    df2.loc[i, 'diff'] = df2.loc[i, 'test'] + df2.loc[i-1, 'diff'] + df2.loc[i-2, 'diff']

# Gauss
num_periods_gauss = 15.5
df2['symbol'] = 2 * math.pi / num_periods_gauss
df2['beta'] = (1 - np.cos(df2['symbol']) ) / ((1.414)**(0.5) - 1)
df2['alpha'] = - df2['beta'] + (df2['beta']**2 + df2['beta'] * 2)**2

# Gauss equation
# initialize
df2.loc[0, 'gauss'] = df2.loc[0, 'close']
df2.loc[1, 'gauss'] = df2.loc[1, 'close']
df2.loc[2, 'gauss'] = df2.loc[2, 'close']
df2.loc[3, 'gauss'] = df2.loc[3, 'close']
df2.loc[4, 'gauss'] = df2.loc[4, 'close']

for i in range (4, len(df2)):
    df2.loc[i, 'gauss'] = df2.loc[i, 'close'] * df2.loc[i, 'alpha']**4 + (4 * (1 - df2.loc[i, 'alpha']))*df2.loc[i-1, 'gauss'] \
                          - (6 * ((1 - df2.loc[i, 'alpha']) ** 2) * df2.loc[i - 2, 'gauss']) \
                          + (4 * (1 - df2.loc[i, 'alpha']) ** 3) * df2.loc[i - 3, 'gauss'] \
                          - ((1 - df2.loc[i, 'alpha']) ** 4) * df2.loc[i - 4, 'gauss']

# ATR
num_periods_ATR = 21
multiplier = 1

df2['ATR_diff'] = df2['high'] - df2['low']
df2['ATR'] = df2['ATR_diff'].ewm(span=num_periods_ATR, adjust=False).mean()

df2['Line'] = df2['gauss']

# upper bands and ATR

df2['upper_band'] = df2['Line'] + multiplier * df2['ATR']
df2['lower_band'] = df2['Line'] - multiplier * df2['ATR']

multiplier_1 = 1.6
multiplier_2 = 2.3

df2['upper_band_1'] = df2['Line'] + multiplier_1 * df2['ATR']
df2['lower_band_1'] = df2['Line'] - multiplier_1 * df2['ATR']

df2['upper_band_2'] = df2['Line'] + multiplier_2 * df2['ATR']
df2['lower_band_2'] = df2['Line'] - multiplier_2 * df2['ATR']

# forecasting begins

# df2['line_change'] = df2['Line'] - df2['Line'].shift(1)
df2['line_change'] = df2['Line'] - df2['Line'].shift(1)
df3 = pd.DataFrame()
df3['date'] = df2['date']
df3['close'] = df2['line_change']
df3['open'] = df2['line_change']
df3['high'] = df2['line_change']
df3['low'] = df2['line_change']

# calculate projection angle
slope_begin_date = '2020-12-15'
slope_end_date = '2021-01-29'
begin_date_index = df3[df3['date'] == slope_begin_date].index.values.astype(int)[0]
end_date_index = df3[df3['date'] == slope_end_date].index.values.astype(int)[0]
print(begin_date_index)
print(end_date_index)
slope_bars = end_date_index - begin_date_index
print(slope_bars)
periods_change = int(slope_bars) # drives the projection by choosing number of periods back
df3['change_SMA'] = TA.SMA(df3, periods_change) # drives the projection

df3.to_csv('sma_change.csv')

slope = df3['change_SMA'].iloc[end_date_index]
print(slope)

# try the loop again

date_diff = df2.loc[len(df2)-1, 'date'] - df2.loc[len(df2)-2, 'date']

# line_diff = df2.loc[len(df2)-1, 'change_SMA']

line_diff = slope

# https://stackoverflow.com/questions/12691551/add-n-business-days-to-a-given-date-ignoring-holidays-and-weekends-in-python

def date_by_adding_business_days(from_date, add_days):
    business_days_to_add = add_days
    current_date = from_date
    while business_days_to_add > 0:
        current_date += timedelta(days=1)
        weekday = current_date.weekday()
        if weekday >= 5: # sunday = 6
            continue
        business_days_to_add -= 1
    return current_date

counter = 0
bars_out = 20
while counter < bars_out:

    df2.loc[len(df2), 'Line'] = df2.loc[len(df2) - 1, 'Line'] + line_diff
    df2.loc[len(df2) - 1, 'date'] = date_by_adding_business_days(df2.loc[len(df2) - 2, 'date'], n)
    counter += 1

ATR = df2.loc[len(df2) - bars_out - 1, 'ATR'] * multiplier
ATR_1 = df2.loc[len(df2) - bars_out - 1, 'ATR'] * multiplier_1
ATR_2 = df2.loc[len(df2) - bars_out - 1, 'ATR'] * multiplier_2

counter1 = 0
while counter1 < bars_out:
    df2.loc[len(df2) - bars_out + counter1-1, 'upper_band_1'] = df2.loc[len(df2) - bars_out - 1 + counter1, 'Line'] + ATR_1
    df2.loc[len(df2) - bars_out + counter1-1, 'lower_band_1'] = df2.loc[len(df2) - bars_out - 1 + counter1, 'Line'] - ATR_1
    df2.loc[len(df2) - bars_out + counter1-1, 'upper_band_2'] = df2.loc[len(df2) - bars_out - 1 + counter1, 'Line'] + ATR_2
    df2.loc[len(df2) - bars_out + counter1-1, 'lower_band_2'] = df2.loc[len(df2) - bars_out - 1 + counter1, 'Line'] - ATR_2
    df2.loc[len(df2) - bars_out + counter1-1, 'upper_band'] = df2.loc[len(df2) - bars_out - 1 + counter1, 'Line'] + ATR
    df2.loc[len(df2) - bars_out + counter1-1, 'lower_band'] = df2.loc[len(df2) - bars_out - 1 + counter1, 'Line'] - ATR

    counter1 += 1

# append dataframe
# https://stackoverflow.com/questions/53304656/difference-between-dates-between-corresponding-rows-in-pandas-dataframe
# https://www.geeksforgeeks.org/how-to-add-one-row-in-an-existing-pandas-dataframe/
# https://stackoverflow.com/questions/10715965/create-pandas-dataframe-by-appending-one-row-at-a-time
# https://stackoverflow.com/questions/49916371/how-to-append-new-row-to-dataframe-in-pandas
# https://stackoverflow.com/questions/50607119/adding-a-new-row-to-a-dataframe-why-loclendf-instead-of-iloclendf
# https://stackoverflow.com/questions/31674557/how-to-append-rows-in-a-pandas-dataframe-in-a-for-loop

fig1 = go.Figure(data=[go.Candlestick(x=df2['date'],
                open=df2['open'],
                high=df2['high'],
                low=df2['low'],
                close=df2['close'], showlegend=True)]

)

fig1.add_trace(
    go.Scatter(
        x=df2['date'],
        y=df2['upper_band'].round(2),
        name='upper band',
        mode="lines",
        line=go.scatter.Line(color="gray"),
        showlegend=True)
)

fig1.add_trace(
    go.Scatter(
        x=df2['date'],
        y=df2['lower_band'].round(2),
        name='lower band',
        mode="lines",
        line=go.scatter.Line(color="gray"),
        showlegend=True)
)

fig1.add_trace(
    go.Scatter(
        x=df2['date'],
        y=df2['upper_band_1'].round(2),
        name='upper band_1',
        mode="lines",
        line=go.scatter.Line(color="gray"),
        showlegend=True)
)

fig1.add_trace(
    go.Scatter(
        x=df2['date'],
        y=df2['lower_band_1'].round(2),
        name='lower band_1',
        mode="lines",
        line=go.scatter.Line(color="gray"),
        showlegend=True)
)

fig1.add_trace(
    go.Scatter(
        x=df2['date'],
        y=df2['upper_band_2'].round(2),
        name='upper band_2',
        mode="lines",
        line=go.scatter.Line(color="gray"),
        showlegend=True)
)

fig1.add_trace(
    go.Scatter(
        x=df2['date'],
        y=df2['lower_band_2'].round(2),
        name='lower band_2',
        mode="lines",
        line=go.scatter.Line(color="gray"),
        showlegend=True)
)



fig1.add_trace(
    go.Scatter(
        x=df2['date'],
        y=df2['Line'].round(2),
        name="WMA",
        mode="lines",
        line=go.scatter.Line(color="blue"),
        showlegend=True)
)



fig1.update_layout(
    title = f'{ticker} Chart', hovermode = 'x unified'
)


fig1.show()
