from utils.utilities import load_portfolio, fetch_stock_history
import pandas as pd
import os, sys
from nsetools import Nse

nse = Nse()


# write a function to return compile all sell triggers
def compile_sell_triggers():
    # create a dictionary to store all sell triggers
    sell_triggers = []
   
    # open portfolio
    portfolio = load_portfolio()

    # create a lit of all tickers in portfolio
    tickers = portfolio["ticker"].tolist()

    # loop through each ticker in portfolio
    for ticker in tickers:
        # load the stock data
        stock_data = fetch_stock_history(ticker)

        # check if stock data is not empty
        if not stock_data.empty:
            # get ema and sma sell triggers
            sell_triggers_ema_sma = sell_trigger_ema_sma(ticker, stock_data)

            # add result triggers to sell triggers
            sell_triggers.extend(sell_triggers_ema_sma)

            # get 52 week high sell trigger
            sell_triggers_52_week_high = sell_trigger_52_week_high(ticker, stock_data)

            # append to sell triggers
            sell_triggers.extend(sell_triggers_52_week_high)

    # convert sell triggers to dataframe
    sell_triggers = pd.DataFrame(sell_triggers)

    # return sell triggers
    return sell_triggers


# write a function that identifies if a sell trigger has been met for 20 EMA and 50 SMA
# if the 20 EMA higher and is within 2% of the 50 SMA, then we have a sell trigger
# return a dictionary of ticker and trigger name
def sell_trigger_ema_sma(ticker, stock_data):
    # create empty dictionary
    sell_triggers_ema_sma = []

    # define three conditions
    # 1. stock price is below 5 day SMA
    # 2. 20 EMA is higher than 50 SMA
    # 3. 20 EMA is within 2% of 50 SMA
    last_price_below_5_sma = False
    ema_above_sma = False
    ema_within_2_percent = False

    # calculate the 5 day SMA
    stock_data["5 SMA"] = stock_data["Close"].rolling(window=5).mean()

    # check if stock price is in downtrend with 5 day SMA
    if stock_data["Close"].iloc[-1] < stock_data["5 SMA"].iloc[-1]:
        last_price_below_5_sma = True

    # calculate the 20 EMA
    stock_data["20 EMA"] = stock_data["Close"].ewm(span=20, adjust=False).mean()

    # calculate the 50 SMA
    stock_data["50 SMA"] = stock_data["Close"].rolling(window=50).mean()

    # calculate the difference between the 20 EMA and 50 SMA
    stock_data["20 EMA - 50 SMA"] = stock_data["20 EMA"] - stock_data["50 SMA"]

    # calculate the percentage difference between the 20 EMA and 50 SMA
    stock_data["20 EMA - 50 SMA %"] = (
        stock_data["20 EMA - 50 SMA"] / stock_data["50 SMA"]
    ) * 100

    # check if 20 EMA is higher than 50 SMA
    if stock_data["20 EMA"].iloc[-1] > stock_data["50 SMA"].iloc[-1]:
        ema_above_sma = True

    # check if 20 EMA is within 2% of 50 SMA
    if stock_data["20 EMA - 50 SMA %"].iloc[-1] < 2:
        ema_within_2_percent = True

    # check if all conditions are met
    if last_price_below_5_sma and ema_above_sma and ema_within_2_percent:
        # add to dictionary

        trigger = {"ticker": ticker, "trigger": "20 EMA and 50 SMA"}
        sell_triggers_ema_sma.append(trigger)

    # return dictionary
    return sell_triggers_ema_sma

# write a function to check if stock price is near 52 week high
# if stock price is within 2% of 52 week high, then we have a sell trigger
# return a dictionary of ticker and trigger name
def sell_trigger_52_week_high(ticker, stock_data):
    # create empty dictionary
    sell_triggers_52_week_high = []

    # calculate the 52 week high
    stock_data["52 Week High"] = stock_data["Close"].rolling(window=252).max()

    # get latest price
    last_price = nse.get_quote(ticker)["lastPrice"]

    # calculate the percentage difference between the last price and 52 week high
    percent_diff = ((last_price - stock_data["52 Week High"].iloc[-1]) / stock_data["52 Week High"].iloc[-1]) * 100

    # check if its uptrend
    if stock_data["Close"].iloc[-1] > stock_data["Close"].iloc[-2]:
        # check if last price is within 2% of 52 week high
        if abs(percent_diff) < 2:
            # add to dictionary
            trigger = {"ticker": ticker, "trigger": f"Near 52 Week High, current diff: {(percent_diff):.2f}%"}
            sell_triggers_52_week_high.append(trigger)

    # return dictionary
    return sell_triggers_52_week_high

# create a function to identify if its a downtrend after achieving high after last golden cross
def sell_trigger_downtrend_after_high(ticker, stock_data):
    # create empty dictionary
    sell_triggers_downtrend_after_high = []

    # calculate 20 EMA and 50 SMA to identify golden cross
    stock_data["20 EMA"] = stock_data["Close"].ewm(span=20, adjust=False).mean()
    stock_data["50 SMA"] = stock_data["Close"].rolling(window=50).mean()

    # check if 20EMA is higher than 50 SMA and also previous days 20 EMA is lower than 50 SMA
    stock_data["Golden Cross"] = (
        (stock_data["20 EMA"] > stock_data["50 SMA"])
        & (stock_data["20 EMA"].shift(1) < stock_data["50 SMA"].shift(1))
    )

    # get the last date when golden cross happened
    last_golden_cross_date = stock_data[stock_data["Golden Cross"] == True].iloc[-1].name

    # find the high after golden cross
    high_after_golden_cross = stock_data[stock_data.index > last_golden_cross_date]["Close"].max()

    # find the date when it happened
    # we will use this date to check if its a downtrend after high
    # if its a downtrend after high, then we have a sell trigger
    date_of_high_after_golden_cross = stock_data[stock_data["Close"] == high_after_golden_cross].index[0]

    # find 3 days EMAs after high
    ema_3_days_after_high = stock_data[stock_data.index > date_of_high_after_golden_cross]["20 EMA"].iloc[:3]

    # check if last price is lower than 3 days EMA
    if stock_data["Close"].iloc[-1] < ema_3_days_after_high.iloc[-1]:
        # add to dictionary
        trigger = {"ticker": ticker, "trigger": "Downtrend after high"}
        sell_triggers_downtrend_after_high.append(trigger)

    # return dictionary
    return sell_triggers_downtrend_after_high