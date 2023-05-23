import pandas as pd
import streamlit as st
import yfinance as yf

from utils.config import Config
from utils.ticker_data import Ticker
from utils.utilities import load_portfolio, save_portfolio

# create a config object
config = Config()
# load config
config = config.load_config()


# create a function to add stock in a popup
def app():
    # create a dictionary to store stock data
    stock_data = {}

    # create a popup to add stock
    with st.form("add_stock", clear_on_submit=True):
        # add a title
        st.title("Add Stock")

        # add a text input to enter ticker and validate it
        ticker = st.text_input("Ticker", key="ticker").upper()

        # add a date input to enter date
        date = st.date_input(
            "Date", key="date", max_value=pd.to_datetime("today").date()
        )
        # add inline columns
        col1, col2 = st.columns(2)
        # add a text input to enter Quantity with minimum value 1
        quantity = col1.number_input("Quantity", key="quantity", min_value=1)
        # add a text input to enter Price with minimum value 1.0
        price = col2.number_input("Price", key="price", min_value=1.0)
        # add a radio button to select transaction type without a default value
        transaction_type = st.radio(
            "Transaction Type", ("Buy", "Sell"), key="transaction_type"
        )

        # add a submit button
        submit = st.form_submit_button("Submit")

    # if submit button is clicked
    if submit:
        # show progress bar
        with st.spinner("Adding stock..."):
            # create a ticker object
            ticker_obj = Ticker(ticker, date, quantity, price, transaction_type)

            stock_data = {
                "ticker": ticker_obj.ticker,
                "company_name": ticker_obj.company_name,
                "date": ticker_obj.date,
                "quantity": ticker_obj.quantity,
                "price": ticker_obj.price,
            }

            # load portfolio
            portfolio = load_portfolio()
            # if portfolio is empty
            if portfolio is None:
                # create a portfolio
                portfolio = pd.DataFrame(
                    columns=["ticker", "company_name", "date", "quantity", "price"]
                )
            # add stock data in portfolio
            portfolio = portfolio.append(stock_data, ignore_index=True)
            # save portfolio
            save_portfolio(portfolio)

            # show success message
            st.success("Stock added successfully")
