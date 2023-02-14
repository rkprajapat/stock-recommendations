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


# create a function to save or retrieve stock scores
@monitor_performance
def get_stock_scores(ticker):
    # get scores file path from config
    scores_file = config.get("scores").get("file_path")

    # check if scores file exists
    if os.path.exists(scores_file):
        # load scores from parquet file loading only for ticker with date column as datetime
        systemLogger.info("Loading scores from file: {} for {}".format(scores_file, ticker))
    
        # load scores from parquet file
        scores = pd.read_parquet(scores_file)

        # check if ticker exists in stock scores
        if ticker in scores["ticker"].values:
            systemLogger.info("Scores found for {}".format(ticker))

            # get stock scores for ticker
            scores = scores[scores["ticker"] == ticker]

            # convert scores date to date type
            scores["date"] = pd.to_datetime(scores["date"])

            # get last traded dates
            (
                _,
                last_traded_date_historical,
            ) = get_last_traded_date()

            # if max date is last trading date, return stock scores
            if scores["date"].max().date() == last_traded_date_historical:
                systemLogger.info("Scores are up to date for {}".format(ticker))
                return scores

    # calculate stock scores
    scores = calculate_stock_scores(ticker)

    # update stock scores to excel file
    update_stock_scores(scores)

    # return stock scores
    return scores


# create a function to update stock scores
@monitor_performance
def update_stock_scores(stock_scores: dict) -> bool:
    # if there are no values in stock scores, return False
    if len(stock_scores) == 0:
        return False

    # get scores file path from config
    scores_file = config.get("scores").get("file_path")

    # check if scores file exists
    if os.path.exists(scores_file):
        # load scores from parquet file
        systemLogger.info("Loading scores from file: {}".format(scores_file))
        scores = pd.read_parquet(scores_file)
        # check if incoming ticker and date exists in scores
        # get incoming ticker
        incoming_ticker = stock_scores["ticker"].values[0]
        # get incoming date and convert to date if datetime
        if isinstance(stock_scores["date"].values[0], datetime):
            incoming_date = stock_scores["date"].values[0].date()
        else:
            incoming_date = stock_scores["date"].values[0]

        # count total rows with incoming ticker and date
        total_rows = scores[
            (scores["ticker"] == incoming_ticker) & (scores["date"] == incoming_date)
        ].shape[0]

        # check if total rows is greater than 1
        if total_rows > 1:
            systemLogger.error("Multiple scores exist for ticker: {} and date: {}".format(incoming_ticker, incoming_date))
            return False
        # check if total rows is 1
        elif total_rows == 1:
            systemLogger.info("Updating scores for ticker: {} and date: {}".format(incoming_ticker, incoming_date))
            # get index of row with incoming ticker and date
            index = scores[
                (scores["ticker"] == incoming_ticker)
                & (scores["date"] == incoming_date)
            ].index[0]

            # find column intersection of columns in scores and incoming scores
            intersection = scores.columns.intersection(stock_scores.columns)

            # update scores with incoming scores using index while scores has more columns than incoming scores
            scores.loc[index, intersection] = stock_scores[intersection].values[0]

        # check if total rows is 0
        elif total_rows == 0:
            systemLogger.info("Adding scores for ticker: {} and date: {}".format(incoming_ticker, incoming_date))
            # concat scores with incoming scores
            scores = pd.concat([scores, stock_scores], ignore_index=True)
    else:
        # create scores from stock scores
        scores = stock_scores

    # save scores to parquet file with partition by ticker and date
    systemLogger.info("Saving scores to file: {}".format(scores_file))
    scores.to_parquet(scores_file, partition_cols=["ticker"], index=False)


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

    # update today's date as date and not datetime
    stock_scores["date"] = datetime.now().date()

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
    stock_scores["piotroski_f_score"] = piotrosky_score(ticker)
    systemLogger.info("Piotrosky score calculated for {}".format(ticker))

    # add to final score if piotrosky score is not None
    if stock_scores["piotroski_f_score"] is not None:
        stock_scores["final_score"] += stock_scores["piotroski_f_score"]

    # convert stock scores to dataframe
    stock_scores = pd.DataFrame(stock_scores, index=[0])

    # update datatype for all columns except ticker and date to float
    stock_score = stock_score.astype(
        {col: np.float32 for col in stock_score.columns if col not in ["ticker", "date"]}
    )

    # return stock scores
    return stock_scores


# write a function to retrieve current quarter piotrosky score
@monitor_performance
def piotrosky_score(ticker):
    # initialize piotrosky score to false
    piotrosky_score = None

    # get scores file path from config
    scores_file = config.get("scores").get("file_path")

    # check if scores file exists
    if os.path.exists(scores_file):
        # load scores from parquet file
        systemLogger.info("Loading scores from parquet file")
        scores = pd.read_parquet(scores_file)

        # Get the current quarter key
        current_quarter = (datetime.now().month - 1) // 3 + 1
        current_year = datetime.now().year
        quarter_key = str(current_year) + "Q" + str(current_quarter)

        # convert date column to date type
        scores["date"] = pd.to_datetime(scores["date"])

        # create a new column in scores dataframe to store quarter key from date column
        scores["quarter_key"] = scores["date"].apply(
            lambda x: str(x.year) + "Q" + str((x.month - 1) // 3 + 1)
        )

        # check if non null piotrosky score is available for this ticker for current quarter
        if (
            len(
                scores[
                    (scores["ticker"] == ticker)
                    & (scores["quarter_key"] == quarter_key)
                    & (scores["piotroski_f_score"].notnull())
                ]
            )
            > 0
        ):
            systemLogger.info("Piotrosky score available for {}".format(ticker))
            # get the piotrosky score for this ticker for current quarter
            piotrosky_score = scores[
                (scores["ticker"] == ticker) & (scores["quarter_key"] == quarter_key)
            ]["piotroski_f_score"].values[0]
        else:
            systemLogger.info("Piotrosky score not available for {}".format(ticker))

    # return piotrosky score
    return piotrosky_score


# write a function to fetch stock history using nsepy
@monitor_performance
def fetch_stock_history(stock_code):
    # create a filename for stock data
    stock_file = f"historical/{stock_code}.xlsx"

    # create empty dataframe for stock data
    stock_data = pd.DataFrame()
    start_date = None

    # check if stock_file exists
    if os.path.exists(stock_file):
        # load existing stock data from excel file
        stock_data = pd.read_excel(stock_file, index_col="Date")

        if len(stock_data) == 0:
            print(f"No Stock Data for {stock_code}")
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
                print(f"{stock_code}: Stock Data is up to date")
                return stock_data

            # calculate start date to date from last date
            start_date = last_date + timedelta(days=1)

            # convert start_date to datetime.date
            start_date = start_date.date()

    # if there is no start_date, create a start_date that is 2 years ago
    if start_date == None:
        start_date = date.today() - timedelta(days=365 * 2)

    # print(f'Getting Stock Data for {stock_code} from {start_date} to {date.today()}')

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

    # check if portfolio file exists
    if not os.path.exists(portfolio_file_path):
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
    print("Saving portfolio to excel file...")

    # check if portfolio is empty
    if portfolio is None:
        return

    # load portfolio file path from config
    portfolio_file_path = config.get("portfolio").get("file_path")

    # save portfolio to excel file
    portfolio.to_excel(portfolio_file_path, index=False)
