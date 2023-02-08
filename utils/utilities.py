import pandas as pd
import os
from datetime import date, datetime, timedelta
from nsepy import get_history

from utils.config import Config

# create a config object
config = Config()
# load config
config = config.load_config()

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