import os
from datetime import date, datetime, time, timedelta
import schedule
import sys
import os
import atexit

import pandas as pd
import pandas_ta as ta
from nsepy import get_history
from pandas_market_calendars import get_calendar
import numpy as np

import utils.technical_analysis as techA
from utils.config import Config
from utils.custom_logger import systemLogger
from utils.perf_monitor import monitor_performance

# create a config object
config = Config()
# load config
config = config.load_config()

# return current and last quarter names
@monitor_performance
def get_quarter_names():
    current_qtr = datetime.now().month // 4 + 1

    # get the current year
    current_qtr_year = datetime.now().year

    # current quarter key
    current_quarter_key = (current_qtr_year, current_qtr)

    # get the previous quarter
    prev_qtr = current_qtr - 1

    # if the previous quarter is 0, then it is the fourth quarter of the previous year
    if prev_qtr == 0:
        prev_qtr = 4
        prev_qtr_year = current_qtr_year - 1
    else:
        prev_qtr_year = current_qtr_year

    # previous quarter key
    prev_quarter_key = (prev_qtr_year, prev_qtr)

    def get_quarter_dates(qtr_key: tuple):
        quarter = qtr_key[1]
        quarter_year = qtr_key[0]

        # get start and end dates for previous quarter
        if quarter == 1:
            quarter_start = datetime(quarter_year, 1, 1)
            quarter_end = datetime(quarter_year, 3, 31)
        elif quarter == 2:
            quarter_start = datetime(quarter_year, 4, 1)
            quarter_end = datetime(quarter_year, 6, 30)
        elif quarter == 3:
            quarter_start = datetime(quarter_year, 7, 1)
            quarter_end = datetime(quarter_year, 9, 30)
        elif quarter == 4:
            quarter_start = datetime(quarter_year, 10, 1)
            quarter_end = datetime(quarter_year, 12, 31)

        quarter_name = 'Q' + str(quarter) + ' ' + str(quarter_year)

        return quarter_name, quarter_start, quarter_end

    return get_quarter_dates(current_quarter_key), get_quarter_dates(prev_quarter_key)

# run a function every day at a specific time
def run_daily_at_time(func, hour, minute):
    schedule.every().day.at("{}:{}".format(hour, minute)).do(func)
    daemonize()
    atexit.register(lambda: os._exit(0))

    while True:
        schedule.run_pending()
        time.sleep(1)
        break

# daemonize the process
def daemonize():
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit()
    except OSError as e:
        sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
        sys.exit(1)

    os.chdir("/")
    os.setsid()
    os.umask(0)

    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
        sys.exit(1)

    sys.stdout.flush()
    sys.stderr.flush()
    si = open(os.devnull, 'r')
    so = open(os.devnull, 'a+')
    se = open(os.devnull, 'a+')
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())

# return the stock code watchlist
@monitor_performance
def get_stock_watchlist():
    # get stock watchlist from config
    stock_watchlist_path = config.get("watchlist").get("file_path")

    # check if stock watchlist exists
    if os.path.exists(stock_watchlist_path):
        systemLogger.info("Loading stock watchlist from file: {}".format(stock_watchlist_path))
        # load stock watchlist from excel file
        stock_watchlist = pd.read_excel(stock_watchlist_path, index_col="ticker")

        systemLogger.info("Stock watchlist loaded for {} stocks".format(len(stock_watchlist)))
    else:
        return None

    # return stock watchlist
    return stock_watchlist

# delte stock scores
@monitor_performance
def delete_stock_scores(ticker):
    # get scores file path from config
    scores_file = config.get("scores").get("file_path")

    # check if scores file exists
    if os.path.exists(scores_file):
        # load scores from parquet file loading only for ticker with date column as datetime
        systemLogger.info("Loading scores from file: {} for {}".format(scores_file, ticker))
    
        # load scores from parquet file using pyarrow engine
        scores = pd.read_parquet(scores_file, engine="pyarrow")

        # check if ticker exists in stock scores
        if ticker in scores["ticker"].values:
            systemLogger.info("Scores found for {}".format(ticker))

            # remove ticker from scores
            scores = scores[scores["ticker"] != ticker]

            # save scores to parquet file
            scores.to_parquet(scores_file, engine="pyarrow")

            systemLogger.info("Scores deleted for {}".format(ticker))

# create a function to save or retrieve stock scores
@monitor_performance
def get_stock_scores(ticker):
    # get scores file path from config
    scores_file = config.get("scores").get("file_path")

    # check if scores file exists
    if os.path.exists(scores_file):
        # load scores from parquet file loading only for ticker with date column as datetime
        systemLogger.info("Loading scores from file: {} for {}".format(scores_file, ticker))
    
        # load scores from parquet file using pyarrow engine
        scores = pd.read_parquet(scores_file, engine="pyarrow")

        # check if ticker exists in stock scores
        if ticker in scores["ticker"].values:
            systemLogger.info("Scores found for {}".format(ticker))

            # get last traded dates
            (
                _,
                last_traded_date_historical,
            ) = get_last_traded_date()

            # get stock scores for ticker and last traded date
            scores = scores[
                (scores["ticker"] == ticker) & (scores["date"] == last_traded_date_historical)
            ]

            # check total records for ticker and last traded date
            total_records = len(scores)
            # if there is only 1 record, return scores
            if total_records == 1:
                return scores

            # if there are more than 1 records, error out and exit
            if total_records > 1:
                systemLogger.error("Multiple scores exist for ticker: {} and date: {}".format(ticker, last_traded_date_historical))
                delete_stock_scores(ticker)
                total_records = 0

            # if there are no records, calculate stock scores
            if total_records == 0:
                # calculate stock scores
                systemLogger.info("Calculating scores for {}".format(ticker))
                scores = calculate_stock_scores(ticker)

                # update stock scores to excel file
                update_stock_scores(scores)

                # return stock scores
                return scores
    
    # calculate stock scores
    systemLogger.info("Score not found for {}".format(ticker))
    scores = calculate_stock_scores(ticker)

    # check if scores is not None
    if scores is not None:
        # update stock scores to excel file
        update_stock_scores(scores)

        # return stock scores
        return scores
    return None


# create a function to update stock scores
@monitor_performance
def update_stock_scores(stock_scores) -> bool:
    # if there are no values in stock scores, return False
    if len(stock_scores) == 0:
        return False

    # get scores file path from config
    scores_file = config.get("scores").get("file_path")

    # create scores directory if it does not exist
    if not os.path.exists(os.path.dirname(scores_file)):
        os.makedirs(os.path.dirname(scores_file))

    # check if scores file exists
    if os.path.exists(scores_file):
        # load scores from parquet file
        systemLogger.info("Loading scores from file: {}".format(scores_file))
        all_scores = pd.read_parquet(scores_file, engine="pyarrow")
        # check if incoming ticker and date exists in scores
        # get incoming ticker
        incoming_ticker = stock_scores["ticker"].values[0]
        # get max date for incoming ticker
        incoming_max_date = stock_scores["date"].values[0]

        # get index of all rows for incoming ticker and date from all scores
        index = all_scores[
            (all_scores["ticker"] == incoming_ticker) & (all_scores["date"] == incoming_max_date)
        ].index

        systemLogger.info("Dropping scores for ticker: {} and date: {}".format(incoming_ticker, incoming_max_date))

        # drop all rows for incoming ticker and date from all scores
        all_scores.drop(index, inplace=True)

        systemLogger.info("Adding scores for ticker: {} and date: {}".format(incoming_ticker, incoming_max_date))
        # add incoming scores to scores
        all_scores = pd.concat([all_scores, stock_scores], ignore_index=True)

    else:
        systemLogger.info("No scores file found. Creating new scores file: {}".format(scores_file))

        # create scores from stock scores
        all_scores = stock_scores

    try:
        # save scores to parquet file with partition by ticker and date
        systemLogger.info("Saving scores to file: {}".format(scores_file))

        all_scores.to_parquet(scores_file, engine="pyarrow")
        return True
    except Exception as e:
        systemLogger.error("Error saving scores to file: {}".format(scores_file))
        return False


# write a function to calculate stock scores
@monitor_performance
def calculate_stock_scores(ticker):
    # create a function to merge scores
    def merge_scores(stock_scores, new_scores):
        # add final score to stock scores
        stock_scores["final_score"] += new_scores["final_score"]

        # add all score columns from new scores to stock scores except final score
        for key in new_scores.keys():
            if key != "final_score":
                stock_scores[key] = new_scores[key]

        return stock_scores

    # fetch stock history
    systemLogger.info("Fetching stock history for {}".format(ticker))
    stock_history = fetch_stock_history(ticker)

    # create empty dataframe
    stock_scores = {}

    # return empty stock scores if stock history is empty
    if len(stock_history) == 0:
        systemLogger.info("Stock history is empty for {}".format(ticker))
        return stock_scores

    # add ticker to stock scores
    stock_scores["ticker"] = ticker

    # add a final score column
    stock_scores["final_score"] = 0

    # get last traded dates
    (
        _,
        last_traded_date_historical,
    ) = get_last_traded_date()

    # update today's date as date and not datetime
    stock_scores["date"] = last_traded_date_historical

    # get moving averages dictionary and append to stock scores while adding final score from moving averages to final score from stock scores
    stock_scores = merge_scores(
        stock_scores, techA.moving_averages_score(stock_history)
    )
    systemLogger.info("Moving averages score calculated for {}".format(ticker))
    stock_scores = merge_scores(stock_scores, techA.macd_score(stock_history))
    systemLogger.info("MACD score calculated for {}".format(ticker))
    stock_scores = merge_scores(stock_scores, techA.rsi_score(stock_history))
    systemLogger.info("RSI score calculated for {}".format(ticker))
    stock_scores = merge_scores(stock_scores, techA.stochastic_score(stock_history))
    systemLogger.info("Stochastic score calculated for {}".format(ticker))
    stock_scores = merge_scores(stock_scores, techA.cci_score(stock_history))
    systemLogger.info("CCI score calculated for {}".format(ticker))
    stock_scores = merge_scores(stock_scores, techA.adx_score(stock_history))
    systemLogger.info("ADX score calculated for {}".format(ticker))
    stock_scores = merge_scores(stock_scores, techA.aroon_score(stock_history))
    systemLogger.info("Aroon score calculated for {}".format(ticker))
    stock_scores = merge_scores(
        stock_scores, techA.ultimate_oscillator_score(stock_history)
    )
    systemLogger.info("Ultimate oscillator score calculated for {}".format(ticker))
    stock_scores = merge_scores(stock_scores, techA.bolinger_band_score(stock_history))
    systemLogger.info("Bolinger band score calculated for {}".format(ticker))
    stock_scores = merge_scores(stock_scores, techA.williams_r_score(stock_history))
    systemLogger.info("Williams R score calculated for {}".format(ticker))
    stock_scores = merge_scores(
        stock_scores, techA.chaikin_oscilator_score(stock_history)
    )
    systemLogger.info("Chaikin oscillator score calculated for {}".format(ticker))
    stock_scores = merge_scores(
        stock_scores, techA.money_flow_index_score(stock_history)
    )
    systemLogger.info("Money flow index score calculated for {}".format(ticker))
    stock_scores = merge_scores(
        stock_scores, techA.on_balance_volume_score(stock_history)
    )
    systemLogger.info("On balance volume score calculated for {}".format(ticker))
    stock_scores = merge_scores(
        stock_scores, techA.detrended_price_oscillator_score(stock_history)
    )
    systemLogger.info("Detrended price oscillator score calculated for {}".format(ticker))
    stock_scores = merge_scores(
        stock_scores, techA.ease_of_movement_score(stock_history)
    )
    systemLogger.info("Ease of movement score calculated for {}".format(ticker))
    stock_scores = merge_scores(
        stock_scores, techA.keltner_channel_score(stock_history)
    )
    systemLogger.info("Keltner channel score calculated for {}".format(ticker))
    stock_scores = merge_scores(stock_scores, techA.mass_index_score(stock_history))
    systemLogger.info("Mass index score calculated for {}".format(ticker))
    stock_scores = merge_scores(
        stock_scores, techA.negative_volume_index_score(stock_history)
    )
    systemLogger.info("Negative volume index score calculated for {}".format(ticker))
    stock_scores = merge_scores(
        stock_scores, techA.positive_volume_index_score(stock_history)
    )
    systemLogger.info("Positive volume index score calculated for {}".format(ticker))
    stock_scores = merge_scores(
        stock_scores, techA.price_volume_trend_score(stock_history)
    )
    systemLogger.info("Price volume trend score calculated for {}".format(ticker))
    stock_scores = merge_scores(stock_scores, techA.rate_of_change_score(stock_history))
    systemLogger.info("Rate of change score calculated for {}".format(ticker))
    stock_scores = merge_scores(stock_scores, techA.true_range_score(stock_history))
    systemLogger.info("True range score calculated for {}".format(ticker))

    # acquire piotrosky score
    # TODO: Remove this after implementing piotrosky score
    # stock_scores["piotroski_f_score"] = piotrosky_score(ticker)

    # # add to final score if piotrosky score is not None
    # if stock_scores["piotroski_f_score"] is not None:
    #     stock_scores["final_score"] += stock_scores["piotroski_f_score"]

    # convert stock scores to dataframe
    stock_scores = pd.DataFrame(stock_scores, index=[0])

    # update datatype for all columns except ticker and date to float
    stock_scores = stock_scores.astype(
        {col: np.float32 for col in stock_scores.columns if col not in ["ticker", "date"]}
    )

    # return stock scores
    return stock_scores

# write a function to fetch stock history using nsepy
@monitor_performance
def fetch_stock_history(stock_code):
    # create a filename for stock data
    stock_file = f"historical/{stock_code}.xlsx"

    # find directory path of the file and create if not exists
    os.makedirs(os.path.dirname(stock_file), exist_ok=True)

    # create empty dataframe for stock data
    stock_data = pd.DataFrame()
    start_date = None

    # check if stock_file exists
    if os.path.exists(stock_file):
        # load existing stock data from excel file
        stock_data = pd.read_excel(stock_file, index_col="Date")

        if len(stock_data) == 0:
            systemLogger.info(
                f"Stock Data for {stock_code} is empty. Fetching data from last 2 years"
            )
            # calculate start date to date from last date
            start_date = date.today() - timedelta(days=365 * 2)
        else:
            # get the last date from the stock data
            last_date = stock_data.index[-1]

            # get last traded dates
            (
                last_traded_date_actual,
                last_traded_date_historical,
            ) = get_last_traded_date()

            # check if last_date is equal to last trading date
            if last_date.date() == last_traded_date_historical:
                systemLogger.info(
                    f"Stock Data for {stock_code} is up to date. Last Date: {last_date.date()}"
                )
                return stock_data

            # calculate start date to date from last date
            start_date = last_date + timedelta(days=1)

            # convert start_date to datetime.date
            start_date = start_date.date()

    # if there is no start_date, create a start_date that is 2 years ago
    if start_date == None:
        start_date = date.today() - timedelta(days=365 * 2)

    # get the stock data
    new_stock_data = get_history(symbol=stock_code, start=start_date, end=date.today())

    # append the stock data to existing stock data using concat
    stock_data = pd.concat([stock_data, new_stock_data])

    # if stock data is empty, return false
    if stock_data.empty:
        return stock_data

    # save stock data to excel file
    stock_data.to_excel(stock_file)

    # sort stock data by date
    stock_data.sort_index(inplace=True)

    # return stock_data
    return stock_data


# write a function to load portfolio from excel file
@monitor_performance
def load_portfolio():
    # load portfolio file path from config
    portfolio_file_path = config.get("portfolio").get("file_path")
    systemLogger.info(f"Portfolio file path: {portfolio_file_path}")

    # check if portfolio file exists
    if not os.path.exists(portfolio_file_path):
        systemLogger.info("Portfolio file does not exist")
        return None

    # load portfolio from excel file
    portfolio = pd.read_excel(portfolio_file_path)

    # check if portfolio is empty
    if portfolio.empty:
        return None

    # return portfolio
    return portfolio


# get last date when nse traded
@monitor_performance
def get_last_traded_date() -> tuple[date, date]:
    """_summary_

    Returns:
        tuple: returns a tuple of actual and historical last trading date
    """

    # Get the Indian trading calendar
    calendar = get_calendar("NSE")

    # find the date five days ago
    today = datetime.now().date()
    five_days_ago = today - timedelta(days=5)

    # find valid trading days between five_days_ago and today
    valid_days = calendar.valid_days(start_date=five_days_ago, end_date=today)
    # find the last trading date
    last_trading_date_actual = max(valid_days).date()

    # check if current time is before 4:00 PM in India then create historical last trading date
    if datetime.now().time() < time(16, 0) and last_trading_date_actual == today:
        last_trading_date_historical = last_trading_date_actual - timedelta(days=1)
    else:
        last_trading_date_historical = last_trading_date_actual

    return last_trading_date_actual, last_trading_date_historical


# write a function to save portfolio to excel file
@monitor_performance
def save_portfolio(portfolio):
    systemLogger.info("Saving portfolio to excel file")

    # check if portfolio is empty
    if portfolio is None:
        return
    
    # find directory path of portfolio file
    portfolio_file_path = config.get("portfolio").get("file_path")
    portfolio_file_dir = os.path.dirname(portfolio_file_path)

    # check if portfolio file directory exists
    if not os.path.exists(portfolio_file_dir):
        # create portfolio file directory
        os.makedirs(portfolio_file_dir)

    # save portfolio to excel file
    portfolio.to_excel(portfolio_file_path, index=False)


# write a function to validate if its a good buy
@monitor_performance
def is_good_buy(ticker):
    try:
        # get the stock data
        stock_history = fetch_stock_history(ticker)

        # check if stock data is empty
        if stock_history.empty:
            return False

        # get the last traded date
        _, last_traded_date_historical = get_last_traded_date()

        # get the last date from the stock data
        last_date = stock_history.index[-1]

        # check if last_date is equal to last trading date
        if last_date.date() != last_traded_date_historical:
            return False

        # if rsi is more than 60, return false
        rsi = ta.rsi(stock_history["Close"], length=14)
        if rsi[-1] > 60:
            return False

        # if macd is negative, return false
        # stock_history["macd"] = (
        #         stock_history["Close"].ewm(span=12, adjust=False).mean()
        #         - stock_history["Close"].ewm(span=26, adjust=False).mean()
        #     )
        # stock_history["macd_signal"] = (
        #         stock_history["macd"].ewm(span=9, adjust=False).mean()
        #     )
        # stock_history["macd_hist"] = stock_history["macd"] - stock_history["macd_signal"]

        # macd = stock_history["macd_hist"]
        # if macd[-1] < 0:
        #     return False
    except:
        systemLogger.exception("Can not check if its a good buy for ticker: " + ticker)
        return False

    return True