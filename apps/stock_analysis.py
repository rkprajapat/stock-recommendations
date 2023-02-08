import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from nsetools import Nse

nse = Nse()

from utils.config import Config
from utils.utilities import load_portfolio, fetch_stock_history
# import from apps folder
from apps.view_portfolio import calculate_total_investment

# create a config object
config = Config()
# load config
config = config.load_config()

# create a function to view stock data
def app():
    # load portfolio
    portfolio = load_portfolio()

    # list tickers
    tickers = portfolio["ticker"].unique().tolist()

    # create a drop down to select stock and clear screen when its value changes
    selected_ticker = st.selectbox("Select a stock", tickers, key="stock_analysis")

    # add a button to load stock history
    if st.button("Load Stock Analysis"):
        # add a progress bar
        with st.spinner("Loading stock analysis..."):
            # load stock history
            stock_history = fetch_stock_history(selected_ticker)

            # if stock history is not available
            if stock_history is None:
                # show an error message
                st.error("Stock history is not available. Please try again later.")
                # exit
                return

    else:
        # exit
        return

    # add a title
    st.title(f"Stock Analysis for {selected_ticker}")

    # show base stats
    load_stock_base_stats(selected_ticker, stock_history)

    # show a candlestick chart of stock history
    load_candlestick_chart(stock_history, selected_ticker)

# load stock base stats such as 52 week high, 52 week low, etc.
def load_stock_base_stats(ticker, history):
    # load stock history
    stock_history = history

    # run a spinner
    with st.spinner("Loading stock base stats..."):
        # get latest quote
        latest_quote = nse.get_quote(ticker)

        # if latest quote is not available
        if not latest_quote:
            # show an error message
            st.error("Latest stock data is not available. Please try again later.")
            # exit
            return

    # get last price
    last_price = latest_quote["lastPrice"]
    # add last price date in first column as a short text
    last_price_date = latest_quote["secDate"]

    # filter stock history for last 52 weeks
    stock_history = stock_history.iloc[-52:]

    # get 52 week high
    week52_high = stock_history["High"].max()
    # calculate how far is last price from 52 week high in percentage
    week52_high_diff = (last_price - week52_high) / week52_high * 100

    # get 52 week low
    week52_low = stock_history["Low"].min()
    # calculate how far is last price from 52 week low
    week52_low_diff = (last_price - week52_low) / week52_low * 100


    # get 52 week average
    week52_avg = stock_history["Close"].mean()
    # calculate how far is last price from 52 week average
    week52_avg_diff = (last_price - week52_avg) / week52_avg * 100

    # add a subheader
    st.subheader("Base Stats")

    # create two columns
    col1, col2 = st.columns(2)

    # add current price in first column
    col1.metric("Last Price", value = f'₹{stock_history["Close"].iloc[-1]}', help=last_price_date)
    # add total traded quantity in first column
    col1.metric("Total Traded Quantity", value = f'{latest_quote["totalTradedVolume"]:,}', help=f'₹{latest_quote["totalTradedValue"]} Lacs')

    # show base stats in second column as 52 Week High (% diff), 52 Week Low (% diff), 52 Week Average (% diff)
    col2.metric("52 Week High", f"₹{week52_high:.2f}", f"{week52_high_diff:.2f}%")
    col2.metric("52 Week Low", f"₹{week52_low:.2f}", f"{week52_low_diff:.2f}%")
    col2.metric("52 Week Average", f"₹{week52_avg:.2f}", f"{week52_avg_diff:.2f}%")


    # show latest quote as json
    # st.subheader("Latest Quote")
    # st.json(latest_quote)


# create plotly candlestick chart
def load_candlestick_chart(history, selected_ticker):
    # load stock history
    stock_history = history

    # add a subheader
    st.subheader("Candlestick Chart")

    # create a candlestick chart
    fig = go.Figure(
        data=[
            go.Candlestick(
                x=stock_history.index,
                open=stock_history["Open"],
                high=stock_history["High"],
                low=stock_history["Low"],
                close=stock_history["Close"],
            )
        ]
    )

    # add spinner
    with st.spinner("Loading candlestick chart..."):
        # load portfolio
        portfolio = load_portfolio()

        # get total investment
        portfolio = calculate_total_investment(portfolio)

        # filter portfolio for selected ticker
        portfolio = portfolio[portfolio["ticker"] == selected_ticker]

        # get average cost from the cell
        avg_cost = portfolio["average_price"].iloc[0]

        # show average cost
        st.write(f"Average Cost: ₹{avg_cost:.2f}")

        # add a horizontal line for average cost
        fig.add_hline(y=avg_cost, line_width=1, line_dash="dash", line_color="red")

    # show candlestick chart
    st.plotly_chart(fig, use_container_width=True)



    