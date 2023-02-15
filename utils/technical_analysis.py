import os
from datetime import date, datetime, time, timedelta, timezone

import numpy as np
import pandas as pd
import pandas_ta as ta
from nsepy import get_history
from pandas_market_calendars import get_calendar

from utils.perf_monitor import monitor_performance


# write a function to get true range score
@monitor_performance
def true_range_score(df):
    # Calculate the TR score
    df["prev_close"] = df["Close"].shift(1)
    df["TR1"] = df[["High", "Low"]].max(axis=1) - df[["High", "Low"]].min(axis=1)
    df["TR2"] = abs(df["High"] - df["prev_close"])
    df["TR3"] = abs(df["Low"] - df["prev_close"])
    df["TR"] = df[["TR1", "TR2", "TR3"]].max(axis=1)

    # Calculate the True Range Score
    df["True Range Score"] = np.where(df["TR"] > df["TR"].shift(1), 1, 0)

    # create empty score dictionary
    scores = {}

    scores["true_range_score"] = df["True Range Score"].iloc[-1]
    scores["final_score"] = scores["true_range_score"]

    return scores


# write a function to get rate of change score
@monitor_performance
def rate_of_change_score(df):
    # Calculate the Rate of Change
    df["Rate of Change"] = ta.roc(df["Close"])

    # Calculate the Rate of Change Score
    df["Rate of Change Score"] = np.where(
        df["Rate of Change"] > df["Rate of Change"].shift(1), 1, 0
    )

    # create empty score dictionary
    scores = {}

    scores["rate_of_change_score"] = df["Rate of Change Score"].iloc[-1]
    scores["final_score"] = scores["rate_of_change_score"]

    return scores


# write a function to get price volume trend score
@monitor_performance
def price_volume_trend_score(df):
    # Calculate the Price Volume Trend
    df["Price Volume Trend"] = ta.pvt(df["Close"], df["Volume"])

    # Calculate the Price Volume Trend Score
    df["Price Volume Trend Score"] = np.where(
        df["Price Volume Trend"] > df["Price Volume Trend"].shift(1), 1, 0
    )

    # create empty score dictionary
    scores = {}

    scores["price_volume_trend_score"] = df["Price Volume Trend Score"].iloc[-1]
    scores["final_score"] = scores["price_volume_trend_score"]

    return scores


# write a function to get positive volume index score
@monitor_performance
def positive_volume_index_score(df):
    # Calculate the Positive Volume Index
    df["Positive Volume Index"] = ta.pvi(df["Close"], df["Volume"])

    # Calculate the Positive Volume Index Score
    df["Positive Volume Index Score"] = np.where(
        df["Positive Volume Index"] > df["Positive Volume Index"].shift(1), 1, 0
    )

    # create empty score dictionary
    scores = {}

    scores["positive_volume_index_score"] = df["Positive Volume Index Score"].iloc[-1]
    scores["final_score"] = scores["positive_volume_index_score"]

    return scores


# write a function to get negative volume index score
@monitor_performance
def negative_volume_index_score(df):
    # Calculate the Negative Volume Index
    df["Negative Volume Index"] = ta.nvi(df["Close"], df["Volume"])

    # Calculate the Negative Volume Index Score
    df["Negative Volume Index Score"] = np.where(
        df["Negative Volume Index"] > df["Negative Volume Index"].shift(1), 1, 0
    )

    # create empty score dictionary
    scores = {}

    scores["negative_volume_index_score"] = df["Negative Volume Index Score"].iloc[-1]
    scores["final_score"] = scores["negative_volume_index_score"]

    return scores


# write a function to get mass index score
@monitor_performance
def mass_index_score(df):
    try:
        # Calculate the high-low range for the current bar and the previous 25 bars
        df["Range"] = df["High"] - df["Low"]
        df["Range_25"] = df["Range"].rolling(window=25).sum()
        df["Range_9"] = df["Range"].rolling(window=9).sum()

        # Calculate the Mass Index
        Mass_Index = df["Range_9"].iloc[-1] / df["Range_25"].iloc[-1]

        # Calculate the Mass Index Score
        Mass_Index_Score = 1 if Mass_Index > 27 else -1 if Mass_Index < 25 else 0
    except:
        Mass_Index_Score = 0

    # create empty score dictionary
    scores = {}

    scores["mass_index_score"] = Mass_Index_Score
    scores["final_score"] = Mass_Index_Score

    return scores


# write a function to get keltner channel score
@monitor_performance
def keltner_channel_score(data):
    try:
        # calculate keltner channel score
        data.ta.kc(append=True)

        # get keltner channel score
        kc_score = (
            1
            if data["KCUe_20_2"].iloc[-1] > data["KCUe_20_2"].iloc[-2]
            else -1
            if data["KCUe_20_2"].iloc[-1] < data["KCUe_20_2"].iloc[-2]
            else 0
        )
    except:
        kc_score = 0

    # create empty score dictionary
    scores = {}

    scores["keltner_channel_score"] = kc_score
    scores["final_score"] = kc_score

    return scores


# write a function to get ease of movement score
@monitor_performance
def ease_of_movement_score(data):
    try:
        # calculate ease of movement score
        data["Distance Moved"] = ((data["High"] + data["Low"]) / 2) - (
            (data["High"].shift(1) + data["Low"].shift(1)) / 2
        )
        data["Box Ratio"] = data["Volume"] / ((data["High"] - data["Low"]) * 1000)
        data["Ease of Movement"] = data["Distance Moved"] / data["Box Ratio"]

        # get ease of movement score
        emv_score = (
            1
            if data["Ease of Movement"].iloc[-1] > data["Ease of Movement"].iloc[-2]
            else -1
            if data["Ease of Movement"].iloc[-1] < data["Ease of Movement"].iloc[-2]
            else 0
        )
    except:
        emv_score = 0

    # create empty score dictionary
    scores = {}

    scores["ease_of_movement_score"] = emv_score
    scores["final_score"] = emv_score

    return scores


# write a function to get distrended price oscillator score
@monitor_performance
def detrended_price_oscillator_score(data):
    try:
        # calculate distrended price oscillator score
        data["DPO"] = ta.dpo(data["Close"], length=20)
        data["DPO_EMA"] = data["DPO"].ewm(span=20, adjust=False).mean()

        # get distrended price oscillator score
        dpo_score = (
            1
            if data["DPO"].iloc[-1] > data["DPO_EMA"].iloc[-1]
            else -1
            if data["DPO"].iloc[-1] < data["DPO_EMA"].iloc[-1]
            else 0
        )
    except:
        dpo_score = 0

    # create empty score dictionary
    scores = {}

    scores["detrended_price_oscillator_score"] = dpo_score
    scores["final_score"] = dpo_score

    return scores


# write a function to get on balance volume score
@monitor_performance
def on_balance_volume_score(data):
    # calculate on balance volume score
    data["OBV"] = ta.obv(data["Close"], data["Volume"])
    data["OBV_EMA"] = data["OBV"].ewm(span=20, adjust=False).mean()

    # get on balance volume score
    obv_score = (
        1
        if data["OBV"].iloc[-1] > data["OBV_EMA"].iloc[-1]
        else -1
        if data["OBV"].iloc[-1] < data["OBV_EMA"].iloc[-1]
        else 0
    )

    # create empty score dictionary
    scores = {}

    scores["on_balance_volume_score"] = obv_score
    scores["final_score"] = scores["on_balance_volume_score"]

    return scores


# write a function to get money flow index score
@monitor_performance
def money_flow_index_score(data):
    # calculate money flow index score
    data["Typical Price"] = (data["High"] + data["Low"] + data["Close"]) / 3
    data["Raw Money Flow"] = data["Typical Price"] * data["Volume"]
    data["Positive Money Flow"] = np.where(
        data["Typical Price"] > data["Typical Price"].shift(1),
        data["Raw Money Flow"],
        0,
    )
    data["Negative Money Flow"] = np.where(
        data["Typical Price"] < data["Typical Price"].shift(1),
        data["Raw Money Flow"],
        0,
    )
    data["Money Flow Ratio"] = (
        data["Positive Money Flow"].rolling(window=14).sum()
        / data["Negative Money Flow"].rolling(window=14).sum()
    )
    data["Money Flow Index"] = 100 - (100 / (1 + data["Money Flow Ratio"]))

    # get money flow index score
    money_flow_index_score = data["Money Flow Index"].iloc[-1]

    # create empty score dictionary
    scores = {}

    scores["money_flow_index_score"] = (
        1 if money_flow_index_score > 80 else -1 if money_flow_index_score < 20 else 0
    )
    scores["final_score"] = scores["money_flow_index_score"]

    return scores


# write a function to get chaiking oscilator score
@monitor_performance
def chaikin_oscilator_score(data):
    # calculate chaiking oscilator score
    window_size = 10
    data["Money Flow"] = data["Close"] * data["Volume"]
    data["High-Low"] = data["High"] - data["Low"]
    data["ADL"] = (
        (2 * data["Close"] - data["High"] - data["Low"])
        / data["High-Low"]
        * data["Money Flow"]
    )
    data["10 Day EMA"] = data["ADL"].ewm(span=window_size).mean()
    data["3 Day EMA"] = data["ADL"].ewm(span=3).mean()
    data["Chaikin Oscillator"] = data["3 Day EMA"] - data["10 Day EMA"]

    # get chaiking oscilator score
    chaiking_oscillator_score = data["Chaikin Oscillator"].iloc[-1]

    # create empty score dictionary
    scores = {}

    scores["chaikin_oscillator_score"] = (
        1
        if chaiking_oscillator_score > 50
        else -1
        if chaiking_oscillator_score < -50
        else 0
    )
    scores["final_score"] = scores["chaikin_oscillator_score"]

    return scores


# write a function to get williams %R score
@monitor_performance
def williams_r_score(stock_history):
    # calculate williams %R score
    window_size = 14
    stock_history["High"] = stock_history["High"].rolling(window=window_size).max()
    stock_history["Low"] = stock_history["Low"].rolling(window=window_size).min()
    stock_history["Williams %R"] = (
        -100
        * (stock_history["Close"] - stock_history["High"])
        / (stock_history["High"] - stock_history["Low"])
    )

    # get williams %R score
    williams_r_score = stock_history["Williams %R"].iloc[-1]

    # create empty score dictionary
    scores = {}

    scores["williams_r_score"] = (
        1 if williams_r_score > -20 else -1 if williams_r_score < -80 else 0
    )
    scores["final_score"] = scores["williams_r_score"]

    return scores


# write a function to get bolinger band score
@monitor_performance
def bolinger_band_score(stock_history):
    try:
        # calculate bolinger band score
        bolinger_band = ta.bbands(
            stock_history["Close"],
            length=20,
            std=2,
            mamode="sma",
            offset=0,
            scalar=100,
        )

        # get last close price
        last_close_price = stock_history["Close"].iloc[-1]

        # get upper and lower band
        upper_band = bolinger_band["BBU_20_2.0"].iloc[-1]
        lower_band = bolinger_band["BBL_20_2.0"].iloc[-1]

        # create a bbands score - 1 if last close price is above upper band, -1 if below lower band, 0 otherwise
        bbands_score = (
            1
            if last_close_price > upper_band
            else -1
            if last_close_price < lower_band
            else 0
        )
    except:
        bbands_score = 0

    # create empty score dictionary
    scores = {}

    scores["bollinger_bands_score"] = bbands_score
    scores["final_score"] = bbands_score

    return scores


# write a function to get ultimate oscillator score
@monitor_performance
def ultimate_oscillator_score(stock_history):
    try:
        # calculate ultimate oscillator score
        ultimate_oscillator = ta.uo(
            stock_history["High"],
            stock_history["Low"],
            stock_history["Close"],
            s=7,
            m=14,
            len=28,
            scalar=100,
        )

        # add ultimate oscillator to stock history
        ultimate_oscillator = 1 if ultimate_oscillator.iloc[-1] > 70 else -1 if ultimate_oscillator.iloc[-1] < 30 else 0
    except:
        ultimate_oscillator = 0

    # create empty score dictionary
    scores = {}

    scores["ultimate_oscillator_score"] = ultimate_oscillator
    scores["final_score"] = ultimate_oscillator

    return scores


# write a function to get aroon score
@monitor_performance
def aroon_score(stock_history):
    try:
        # calculate aroon score
        aroon = ta.aroon(
            stock_history["High"],
            stock_history["Low"],
            length=25,
            scalar=100,
        )

        # add aroon to stock history
        aroon = 1 if aroon["AROONOSC_25"].iloc[-1] > 50 else -1 if aroon["AROONOSC_25"].iloc[-1] < -50 else 0
    except:
        aroon = 0

    # create empty score dictionary
    scores = {}

    scores["aroon_score"] = aroon
    scores["final_score"] = aroon

    return scores


# write a function to get adx score
@monitor_performance
def adx_score(stock_history):
    try:
        # calculate adx score
        adx = ta.adx(
            stock_history["High"],
            stock_history["Low"],
            stock_history["Close"],
            length=14,
            scalar=100,
        )

        # add adx to stock history
        adx = 1 if adx["ADX_14"].iloc[-1] > 75 else -1 if adx["ADX_14"].iloc[-1] < 25 else 0
    except:
        adx = 0

    # create empty score dictionary
    scores = {}

    scores["adx_score"] = adx
    scores["final_score"] = adx

    return scores


# create a function to get cci score
@monitor_performance
def cci_score(stock_history):
    try:
        # calculate cci score
        cci = ta.cci(
            stock_history["High"],
            stock_history["Low"],
            stock_history["Close"],
            length=20,
            scalar=0.015,
        )

        # add cci to stock history
        cci = 1 if cci.iloc[-1] > 100 else -1 if cci.iloc[-1] < -100 else 0

    except:
        cci = 0

    # create empty score dictionary
    scores = {}

    scores["cci_score"] = cci
    scores["final_score"] = cci

    return scores


# create a function to get stochasitc score
@monitor_performance
def stochastic_score(stock_history):
    try:
        # calculate stochastic score
        sch = ta.stoch(
            stock_history["High"],
            stock_history["Low"],
            stock_history["Close"],
            length=14,
            smooth_k=3,
            smooth_d=3,
        )

        sch = 1 if sch['STOCHk_14_3_3'].iloc[-1] > 80 else -1 if sch['STOCHk_14_3_3'].iloc[-1] < 20 else 0

    except:
        sch = 0

    # create empty score dictionary
    scores = {}

    scores["stochastic_score"] = sch
    scores["final_score"] = sch

    return scores


# create a function to get rsi score
@monitor_performance
def rsi_score(stock_history):
    try:
        # calculate rsi score
        stock_history["rsi"] = ta.rsi(stock_history["Close"], length=14)

        # calculate rsi score
        rsi = 1 if stock_history["rsi"].iloc[-1] > 70 else -1 if stock_history["rsi"].iloc[-1] < 30 else 0
    except:
        rsi = 0

    # create empty score dictionary
    scores = {}

    scores["rsi_score"] = rsi
    scores["final_score"] = rsi

    return scores


# create a function to get macd score
@monitor_performance
def macd_score(stock_history):
    try:
        # calculate macd score
        stock_history["macd"] = (
            stock_history["Close"].ewm(span=12, adjust=False).mean()
            - stock_history["Close"].ewm(span=26, adjust=False).mean()
        )
        stock_history["macd_signal"] = (
            stock_history["macd"].ewm(span=9, adjust=False).mean()
        )
        stock_history["macd_hist"] = stock_history["macd"] - stock_history["macd_signal"]

        # calculate macd score
        macd = 1 if stock_history["macd_hist"].iloc[-1] > 0 else 0
    except:
        macd = 0

    # create empty score dictionary
    scores = {}

    scores["macd_score"] = macd
    scores["final_score"] = macd

    return scores


# create a function to get moving averages score
@monitor_performance
def moving_averages_score(stock_history):
    # calculate 20 day moving average
    stock_history["20d"] = (
        stock_history["Close"].rolling(window=20, min_periods=1).mean()
    )

    # calculate 50 day moving average
    stock_history["50d"] = (
        stock_history["Close"].rolling(window=50, min_periods=1).mean()
    )

    # calculate 200 day moving average
    stock_history["200d"] = (
        stock_history["Close"].rolling(window=200, min_periods=1).mean()
    )

    # calculate 20 day moving average
    stock_history["20d_50d"] = stock_history["20d"] - stock_history["50d"]

    # calculate 50 day moving average
    stock_history["50d_200d"] = stock_history["50d"] - stock_history["200d"]

    # calculate 20d_50d score
    stock_history["20d_50d_Score"] = stock_history["20d_50d"].apply(
        lambda x: 1 if x > 0 else 0
    )

    # calculate 50d_200d score
    stock_history["50d_200d_Score"] = stock_history["50d_200d"].apply(
        lambda x: 1 if x > 0 else 0
    )

    # calculate 20d_50d_200d score
    stock_history["20d_50d_200d_Score"] = (
        stock_history["20d_50d_Score"] + stock_history["50d_200d_Score"]
    )

    # calculate 20d_50d_200d score
    stock_history["20d_50d_200d_Score"] = stock_history["20d_50d_200d_Score"].apply(
        lambda x: 1 if x == 2 else 0
    )

    # calculate 20d_50d_200d score
    stock_history["20d_50d_200d_Score"] = stock_history["20d_50d_200d_Score"].shift(1)

    # calculate 20d_50d_200d score
    stock_history["20d_50d_200d_Score"] = stock_history["20d_50d_200d_Score"].fillna(0)

    # create empty score dictionary
    scores = {}

    # add all scores to stock scores
    scores["20d_50d_Score"] = stock_history["20d_50d_200d_Score"].iloc[-1]
    scores["50d_200d_Score"] = stock_history["50d_200d_Score"].iloc[-1]
    scores["20d_50d_200d_Score"] = stock_history["20d_50d_200d_Score"].iloc[-1]

    # calculate final score
    scores["final_score"] = (
        scores["20d_50d_Score"]
        + scores["50d_200d_Score"]
        + scores["20d_50d_200d_Score"]
    )

    return scores
