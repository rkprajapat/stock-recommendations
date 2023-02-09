import streamlit as st
import pandas as pd
import base64
from nsetools import Nse

nse = Nse()

from utils.config import Config
from utils.utilities import load_portfolio

# create a config object
config = Config()
# load config
config = config.load_config()

# write a function to calculate total investment
def calculate_total_investment(portfolio):
    # create empty dataframe
    agg_portfolio = pd.DataFrame()

    # identify holding tickers where sum of total quantity is greater than 0
    agg_portfolio = portfolio.groupby("ticker").agg({"quantity": "sum"})
    agg_portfolio = agg_portfolio[agg_portfolio["quantity"] > 0]
    agg_portfolio = agg_portfolio.reset_index()

    # get holding tickers
    holding_tickers = agg_portfolio["ticker"].tolist()


    # filter portfolio to keep only holding tickers
    portfolio = portfolio[portfolio["ticker"].isin(holding_tickers)]

    # calculate a multiplier for each transaction
    portfolio["multiplier"] = portfolio["quantity"] * portfolio["price"]

    # calculate total quantity, average price and total investment by ticker
    agg_portfolio = portfolio.groupby(["ticker","company_name"]).agg(
        {
            "quantity": "sum",
            "price": "mean",
            "multiplier": "sum",
        }
    )

    # calculate average price
    agg_portfolio["average_price"] = agg_portfolio["multiplier"] / agg_portfolio["quantity"]

    # drop multiplier and price columns
    agg_portfolio = agg_portfolio.drop(["multiplier", "price"], axis=1)

    # calculate total investment
    agg_portfolio["total_investment"] = agg_portfolio["quantity"] * agg_portfolio["average_price"]

    # get latest price
    agg_portfolio["latest_price"] = agg_portfolio.index.get_level_values("ticker").map(
        lambda x: nse.get_quote(x)["lastPrice"]
    )

    # calculate current value
    agg_portfolio["current_value"] = agg_portfolio["quantity"] * agg_portfolio["latest_price"]

    # calculate profit/loss
    agg_portfolio["profit/loss"] = agg_portfolio["current_value"] - agg_portfolio["total_investment"]

    # calculate profit/loss percentage
    agg_portfolio["profit/loss percentage"] = (
        agg_portfolio["profit/loss"] / agg_portfolio["total_investment"]
    ) * 100

    # sort by profit/loss percentage
    agg_portfolio = agg_portfolio.sort_values("profit/loss percentage", ascending=False)

    # reset index
    agg_portfolio = agg_portfolio.reset_index()

    # reset index
    agg_portfolio = agg_portfolio.reset_index(drop=True)
    agg_portfolio.index = agg_portfolio.index + 1

    return agg_portfolio

# create a function to display portfolio
def display_portfolio(portfolio):
    # calculate total investment
    portfolio = calculate_total_investment(portfolio)

    # remove underscore from column names and capitalize each word
    portfolio.columns = portfolio.columns.str.replace("_", " ").str.title()

    # calculate total investment
    total_investment = portfolio["Total Investment"].sum()

    # calculate current value
    current_value = portfolio["Current Value"].sum()

    # calculate profit/loss
    profit_loss = current_value - total_investment

    # calculate profit/loss percentage
    profit_loss_percentage = (profit_loss / total_investment) * 100

    # list of columns to round off
    columns_to_round_off = [
        "average_price",
        "total_investment",
        "latest_price",
        "current_value",
        "profit/loss",
    ]
    columns_to_round_off = [str(x).replace("_", " ").title() for x in columns_to_round_off]

    # style dataframe columns to display currency and percentage
    portfolio[columns_to_round_off] = portfolio[columns_to_round_off].applymap(
        lambda x: "₹{:.2f}".format(x) if isinstance(x, float) else x
    )

    # style percentage column to display percentage
    portfolio["Profit/Loss Percentage"] = portfolio["Profit/Loss Percentage"].map(
        lambda x: "{:.2%}".format(x/100)
    )

    # show portfolio with full height
    st.dataframe(portfolio)

    # display total investment
    st.markdown(
        f"**Total Investment:** ₹{total_investment:.2f}",
        unsafe_allow_html=True,
    )

    # display current value
    st.markdown(
        f"**Current Value:** ₹{current_value:.2f}",
        unsafe_allow_html=True,
    )

    st.metric(
        label="Profit/Loss",
        value=f"₹{profit_loss:.2f}",
        delta=f"{profit_loss_percentage:.2f}%",
    )

    # add a button to download portfolio
    download = st.button("Download Portfolio")

    # if download button is clicked
    if download:
        # download portfolio
        st.markdown(
            get_table_download_link(portfolio, "portfolio.csv"),
            unsafe_allow_html=True,
        )


# create a function to get download link
def get_table_download_link(df, filename):
    # convert dataframe to csv
    csv = df.to_csv(index=False)
    # encode csv
    b64 = base64.b64encode(csv.encode()).decode()
    # create download link
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Download csv file</a>'
    return href
    

def app():
    # add a title
    st.title("Portfolio")

    # add spinner
    with st.spinner("Loading Portfolio..."):
        # load portfolio
        portfolio = load_portfolio()

        # if portfolio is empty
        if portfolio is None:
            # show error message
            st.error("Portfolio is empty")
        else:
            # display portfolio
            display_portfolio(portfolio)

