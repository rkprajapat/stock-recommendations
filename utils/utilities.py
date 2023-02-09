import pandas as pd
import os
from datetime import date, datetime, timedelta
from nsepy import get_history

from utils.config import Config

# create a config object
config = Config()
# load config
config = config.load_config()

# create a function to save or retrieve stock scores
def get_stock_scores(ticker, stock_history):
    # get scores file path from config
    scores_file = config.get['scores'].get('file_path')

    # check if scores file exists
    if os.path.exists(scores_file):
        # load scores from excel file
        stock_scores = pd.read_excel(scores_file, index_col='Date')
    else:
        # create empty excel file
        stock_scores = pd.DataFrame()
        stock_scores.to_excel(scores_file)
    
    stock_scorer = {
        'ticker': ticker,
        'date': "",
        '20d_50d_Score': 0,
        '50d_200d_Score': 0,
        '20d_50d_200d_Score': 0,
        'pietroski_f_score': 0,
        'macd_score': 0,
        'rsi_score': 0,
        'stochastic_score': 0,
        'cci_score': 0,
        'adx_score': 0,
        'aroon_score': 0,
        'ultimate_oscillator_score': 0,
        'williams_r_score': 0,
        'bollinger_bands_score': 0,
        'chaikin_oscillator_score': 0,
        'money_flow_index_score': 0,
        'on_balance_volume_score': 0,
        'average_directional_index_score': 0,
        'average_directional_movement_score': 0,
        'commodity_channel_index_score': 0,
        'detrended_price_oscillator_score': 0,
        'ease_of_movement_score': 0,
        'force_index_score': 0,
        'keltner_channel_score': 0,
        'mass_index_score': 0,
        'negative_volume_index_score': 0,
        'on_balance_volume_mean_score': 0,
        'positive_volume_index_score': 0,
        'price_volume_trend_score': 0,
        'rate_of_change_score': 0,
        'relative_strength_index_score': 0,
        'stochastic_oscillator_score': 0,
        'true_range_score': 0,
    }

    # add ticker to stock_scorer
    stock_scorer['ticker'] = ticker

    # Add today's date to stock_scorer
    stock_scorer['date'] = datetime.now().date()

    # create a dataframe from stock_scorer
    stock_scorer = pd.DataFrame(stock_scorer, index=[0])

    # append to stock scores
    stock_scores = stock_scores.append(stock_scorer, ignore_index=True)

    # save stock scores to excel file
    stock_scores.to_excel(scores_file)
    

# write a function to calculate stock scores
def calculate_stock_scores(ticker, stock_history):
    # create empty dataframe
    stock_scores = pd.DataFrame()

    # calculate 20 day moving average
    stock_history['20d'] = stock_history['Close'].rolling(window=20, min_periods=1).mean()

    # calculate 50 day moving average
    stock_history['50d'] = stock_history['Close'].rolling(window=50, min_periods=1).mean()

    # calculate 200 day moving average
    stock_history['200d'] = stock_history['Close'].rolling(window=200, min_periods=1).mean()

    # calculate 20 day moving average
    stock_history['20d_50d'] = stock_history['20d'] - stock_history['50d']

    # calculate 50 day moving average
    stock_history['50d_200d'] = stock_history['50d'] - stock_history['200d']

    # calculate 20d_50d score
    stock_history['20d_50d_Score'] = stock_history['20d_50d'].apply(lambda x: 1 if x > 0 else 0)

    # calculate 50d_200d score
    stock_history['50d_200d_Score'] = stock_history['50d_200d'].apply(lambda x: 1 if x > 0 else 0)

    # calculate 20d_50d_200d score
    stock_history['20d_50d_200d_Score'] = stock_history['20d_50d_Score'] + stock_history['50d_200d_Score']

    # calculate 20d_50d_200d score
    stock_history['20d_50d_200d_Score'] = stock_history['20d_50d_200d_Score'].apply(lambda x: 1 if x == 2 else 0)

    # calculate 20d_50d_200d score
    stock_history['20d_50d_200d_Score'] = stock_history['20d_50d_200d_Score'].shift(1)

    # calculate 20d_50d_200d score
    stock_history['20d_50d_200d_Score'] = stock_history['20d_50d_200d_Score'].fillna(0)

# write a function to fetch stock history using nsepy
def fetch_stock_history(stock_code):
    # create a filename for stock data
    stock_file = f'historical/{stock_code}.xlsx'
    
    # create empty dataframe for stock data
    stock_data = pd.DataFrame()
    start_date = None
    
    # check if stock_file exists
    if os.path.exists(stock_file):
        # load existing stock data from excel file
        stock_data = pd.read_excel(stock_file, index_col='Date')
        
        if len(stock_data) == 0:
            print(f'No Stock Data for {stock_code}')
            # calculate start date to date from last date
            start_date = date.today() - timedelta(days=365*2)
        else:
            # get the last date from the stock data
            last_date = stock_data.index[-1]
            
            # check if last_date is today
            if last_date == pd.to_datetime('today').date():
                print(f'{stock_code}: Stock Data is up to date')
                return stock_data
    
            # calculate start date to date from last date
            start_date = last_date + timedelta(days=1)
            
            # convert start_date to datetime.date
            start_date = start_date.date()
    
    # if there is no start_date, create a start_date that is 2 years ago
    if start_date == None:
        start_date = date.today() - timedelta(days=365*2)

    # print(f'Getting Stock Data for {stock_code} from {start_date} to {date.today()}')
    
    # get the stock data
    new_stock_data = get_history(symbol=stock_code, start=start_date, end=date.today())
    
    # append the stock data to existing stock data
    stock_data = stock_data.append(new_stock_data)

    # save stock data to excel file
    stock_data.to_excel(stock_file)

    # sort stock data by date
    stock_data.sort_index(inplace=True)
    
    # return stock_data
    return stock_data

# write a function to load portfolio from excel file
def load_portfolio():
    # load portfolio file path from config
    portfolio_file_path = config.get('portfolio').get('file_path')

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

# write a function to save portfolio to excel file
def save_portfolio(portfolio):
    print('Saving portfolio to excel file...')

    # check if portfolio is empty
    if portfolio is None:
        return

    # load portfolio file path from config
    portfolio_file_path = config.get('portfolio').get('file_path')

    # save portfolio to excel file
    portfolio.to_excel(portfolio_file_path, index=False)