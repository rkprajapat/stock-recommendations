import streamlit as st
import pandas as pd
from nsetools import Nse

nse = Nse()

from utils.config import Config
from utils.utilities import load_portfolio, save_portfolio

# create a config object
config = Config()
# load config
config = config.load_config()

# create a function to validate ticker
def validate_ticker(ticker):
    if nse.is_valid_code(ticker):
        return True
    return False


# create a function to add stock in a popup
def app():
    # create a dictionary to store stock data
    stock_data = {}

    # create a popup to add stock
    with st.form("add_stock"):
        # add a title
        st.title("Add Stock")

        # add a text input to enter ticker and validate it
        ticker = st.text_input("Ticker", key="ticker")
        # add a date input to enter date
        date = st.date_input("Date", key="date", max_value=pd.to_datetime("today").date())
        # add inline columns
        col1, col2 = st.columns(2)
        # add a text input to enter Quantity with minimum value 1
        quantity = col1.number_input("Quantity", key="quantity", min_value=1)
        # add a text input to enter Price with minimum value 1.0
        price = col2.number_input("Price", key="price", min_value=1.0)
        # add a radio button to select transaction type without a default value
        transaction_type = st.radio("Transaction Type", ("Buy", "Sell"), key="transaction_type")

        # add a submit button
        submit = st.form_submit_button("Submit")

    # if submit button is clicked
    if submit:
        # show progress bar
        with st.spinner("Adding stock..."):

            # if ticker is valid
            if validate_ticker(ticker):
                # add ticker in stock data
                stock_data["ticker"] = ticker
                # add company name in stock data
                stock_data["company_name"] = nse.get_quote(ticker)["companyName"]
                # add date in stock data
                stock_data["date"] = date
                # add quantity in stock data based on transaction type
                if transaction_type == "Buy":
                    stock_data["quantity"] = quantity
                else:
                    stock_data["quantity"] = -quantity
                
                # add price in stock data
                stock_data["price"] = price

                # capitalize all columns
                stock_data["company_name"] = stock_data["company_name"].capitalize()
                # capitalize ticker
                stock_data["ticker"] = stock_data["ticker"].upper()
                # round off price to 2 decimal places
                stock_data["price"] = round(stock_data["price"], 2)
                # change quantity to integer
                stock_data["quantity"] = int(stock_data["quantity"])

                # load portfolio
                portfolio = load_portfolio()
                # if portfolio is empty
                if portfolio is None:
                    # create a portfolio
                    portfolio = pd.DataFrame(columns=["ticker", "date", "quantity", "price"])
                # add stock data in portfolio
                portfolio = portfolio.append(stock_data, ignore_index=True)
                # save portfolio
                save_portfolio(portfolio)
                # show success message
                st.success("Stock added successfully")
            else:
                # show error message
                st.error("Invalid ticker")
