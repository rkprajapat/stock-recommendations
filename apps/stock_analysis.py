import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from nsetools import Nse
import pandas_ta as ta


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

            # filter for last 1 year by index date and 1 year delta from today
            stock_history = stock_history[
                (stock_history.index >= pd.Timestamp.today() - pd.Timedelta(days=365))
                & (stock_history.index <= pd.Timestamp.today())
            ]

            # show date range
            st.write(
                f"Showing data from {stock_history.index[0].strftime('%d %b %Y')} to {stock_history.index[-1].strftime('%d %b %Y')}"
            )

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

    # show rsi chart
    rsi_chart(stock_history, selected_ticker)

    # show macd chart
    macd_chart(stock_history, selected_ticker)

    # show bollinger band chart
    bollinger_band_chart(stock_history, selected_ticker)

    # show moving average chart
    moving_average_chart(stock_history, selected_ticker)


# write a function to show bollinger band chart
def bollinger_band_chart(stock_history, ticker):
    # add a subheader
    st.subheader("Bollinger Bands")

    # explain bollinger bands
    st.markdown(
        "Bollinger Bands are volatility bands placed above and below a moving average. Volatility is based on the standard deviation, which changes as volatility increases and decreases. The bands automatically widen when volatility increases and narrow when volatility decreases. This dynamic nature of Bollinger Bands also means they can be used on different securities with the standard settings."
    )

    # add a progress bar
    with st.spinner("Loading Bollinger Bands chart..."):
        # calculate bollinger bands
        bollinger_bands = stock_history.ta.bbands(
            close="Close", length=20, std=2, append=True
        )

        # create a figure
        fig = go.Figure()

        # add candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=stock_history.index,
                open=stock_history["Open"],
                high=stock_history["High"],
                low=stock_history["Low"],
                close=stock_history["Close"],
                name="Candlestick",
            )
        )

        # add bollinger bands
        fig.add_trace(
            go.Scatter(
                x=stock_history.index,
                y=bollinger_bands["BBU_20_2.0"],
                name="Upper Bollinger Band",
                line=dict(color="red"),
                # add line width
                line_width=1,
            )
        )

        fig.add_trace(
            go.Scatter(
                x=stock_history.index,
                y=bollinger_bands["BBL_20_2.0"],
                name="Lower Bollinger Band",
                line=dict(color="red"),
                # add line width
                line_width=1,
            )
        )

        # show legend on top
        fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        # show the figure
        st.plotly_chart(fig, use_container_width=True)


# write a function to show macd chart
def macd_chart(stock_history, ticker):
    # add a subheader
    st.subheader("MACD")

    # explain macd
    st.markdown(
        "MACD is a trend-following momentum indicator that shows the relationship between two moving averages of prices. The MACD is calculated by subtracting the 26-period Exponential Moving Average (EMA) from the 12-period EMA. A nine-day EMA of the MACD, called the 'signal line', is then plotted on top of the MACD, functioning as a trigger for buy and sell signals. Traders may buy the security when the MACD crosses above its signal line and sell - or short - the security when the MACD crosses below the signal line."
    )

    st.markdown(
        "The MACD is considered to be bullish when it is above its signal line and bearish when it is below the signal line. The MACD can also be used to identify divergences, price extremes, and changes in momentum."
    )

    # add a progress bar
    with st.spinner("Loading MACD chart..."):
        # calculate macd
        macd = stock_history.ta.macd(fast=12, slow=26, signal=9, append=True)

        # create a figure
        fig = go.Figure()

        # add macd line
        fig.add_trace(
            go.Scatter(
                x=stock_history.index,
                y=macd["MACD_12_26_9"],
                name="MACD",
                line=dict(color="blue", width=1),
            )
        )

        # add signal line
        fig.add_trace(
            go.Scatter(
                x=stock_history.index,
                y=macd["MACDh_12_26_9"],
                name="Signal",
                line=dict(color="red", width=1),
            )
        )

        # add histogram
        fig.add_trace(
            go.Bar(x=stock_history.index, y=macd["MACDs_12_26_9"], name="Histogram")
        )

        # show legend on top
        fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        # show the chart
        st.plotly_chart(fig, use_container_width=True)


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

    # get today's change
    today_change = latest_quote["change"]
    # get today's change percentage
    today_change_percentage = latest_quote["pChange"]



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

    # show last price date
    st.markdown(f"Last Price Date: {last_price_date}")

    # create two columns
    col1, col2 = st.columns(2)

    # add current price in first column
    col1.metric(
        "Last Price", value=f'₹{stock_history["Close"].iloc[-1]}'
    )

    # add today's change in first column
    col1.metric(
        "Today's Change",
        value=f'₹{today_change}',
        delta=f'{today_change_percentage}%',
    )

    # add total traded quantity in first column
    col1.metric(
        "Total Traded Quantity",
        value=f'{latest_quote["totalTradedVolume"]:,}',
        help=f'₹{latest_quote["totalTradedValue"]} Lacs',
    )

    # show base stats in second column as 52 Week High (% diff), 52 Week Low (% diff), 52 Week Average (% diff)
    col2.metric("52 Week High", f"₹{week52_high:.2f}", f"{week52_high_diff:.2f}%")
    col2.metric("52 Week Low", f"₹{week52_low:.2f}", f"{week52_low_diff:.2f}%")
    col2.metric("52 Week Average", f"₹{week52_avg:.2f}", f"{week52_avg_diff:.2f}%")

    # show columns border
    st.markdown("---")


# calculate average cost of a stock
def get_average_cost(ticker):
    # load portfolio
    portfolio = load_portfolio()

    # get total investment
    portfolio = calculate_total_investment(portfolio)

    # filter portfolio for selected ticker
    portfolio = portfolio[portfolio["ticker"] == ticker]

    # get average cost from the cell
    avg_cost = portfolio["average_price"].iloc[0]

    # return average cost
    return avg_cost


# create plotly candlestick chart
def load_candlestick_chart(history, selected_ticker):
    # load stock history
    stock_history = history

    # add a subheader
    st.subheader("Candlestick Chart")

    # add a spinner
    with st.spinner("Loading candlestick chart..."):
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

        # get average cost
        avg_cost = get_average_cost(selected_ticker)

        # if average cost is available
        if avg_cost:
            # show average cost
            st.write(f"Average Cost: ₹{avg_cost:.2f}")

            # add a horizontal line for average cost
            fig.add_hline(y=avg_cost, line_width=1, line_dash="dash", line_color="red")

        # show candlestick chart
        st.plotly_chart(fig, use_container_width=True)


# write a function to show rsi chart
def rsi_chart(history, selected_ticker):
    # load stock history
    stock_history = history

    # add a subheader
    st.subheader("RSI Chart")

    # explain rsi
    st.markdown(
        "The relative strength index (RSI) is a momentum indicator used in technical analysis. \
    RSI measures the speed and magnitude of a security's recent price changes to \
    evaluate overvalued or undervalued conditions in the price of that security. \
    The RSI is displayed as an oscillator (a line graph that moves between two extremes) \
    and can have a reading from 0 to 100. \
    The RSI is considered overbought when above 70 and oversold when below 30. \
    The RSI is most effective when charted with other technical indicators that confirm trends. \
    "
    )

    # add a spinner
    with st.spinner("Loading RSI chart..."):
        # calculate rsi
        rsi = ta.momentum.rsi(stock_history["Close"], window=14, fillna=True)

        # add rsi to stock history
        stock_history["RSI"] = rsi

        # calculate rsi crossover
        stock_history["RSI_Crossover"] = stock_history.apply(
            lambda x: 1 if x["RSI"] < 30 else 0, axis=1
        )

        # create a plotly chart
        fig = go.Figure()

        # add rsi line
        fig.add_trace(
            go.Scatter(
                x=stock_history.index,
                y=stock_history["RSI"],
                name="RSI",
                line=dict(color="blue", width=2),
            )
        )

        # add a horizontal line for 30
        fig.add_hline(y=30, line_width=1, line_dash="dash", line_color="red")

        # add a horizontal line for 70
        fig.add_hline(y=70, line_width=1, line_dash="dash", line_color="red")

        # show rsi chart
        st.plotly_chart(fig, use_container_width=True)


# write a function to load moving average chart
def moving_average_chart(history, selected_ticker):
    # load stock history
    stock_history = history

    # add a subheader
    st.subheader("Moving Average Chart")

    # add a spinner
    with st.spinner("Loading moving average chart..."):
        # calculate moving average
        moving_average = stock_history["Close"].rolling(window=50).mean()
        # calculate exponential moving average
        exponential_moving_average = history["Close"].ewm(span=20, adjust=False).mean()

        # add moving average and exponential moving average to stock history
        stock_history["SMA50"] = moving_average
        stock_history["EMA20"] = exponential_moving_average

        # calculate moving average crossover
        stock_history["MA_Crossover"] = stock_history.apply(
            lambda x: 1 if x["SMA50"] > x["EMA20"] else 0, axis=1
        )

        # calculate moving average crossover signal
        stock_history["MA_Crossover_Signal"] = stock_history["MA_Crossover"].diff()

        # create a moving average chart
        fig = go.Figure(
            data=[
                go.Scatter(
                    x=stock_history.index, y=stock_history["Close"], name="Close"
                ),
                go.Scatter(
                    x=stock_history.index, y=stock_history["SMA50"], name="SMA50"
                ),
                go.Scatter(
                    x=stock_history.index, y=stock_history["EMA20"], name="EMA20"
                ),
            ]
        )

        # add markers on moving average crossover
        fig.add_trace(
            go.Scatter(
                x=stock_history[stock_history["MA_Crossover_Signal"] == -1].index,
                y=stock_history[stock_history["MA_Crossover_Signal"] == -1]["SMA50"],
                mode="markers",
                marker=dict(color="green", size=10),
                name="Buy Signal",
            )
        )

        # add markers on moving average crossover
        fig.add_trace(
            go.Scatter(
                x=stock_history[stock_history["MA_Crossover_Signal"] == 1].index,
                y=stock_history[stock_history["MA_Crossover_Signal"] == 1]["SMA50"],
                mode="markers",
                marker=dict(color="red", size=10),
                name="Sell Signal",
            )
        )

        # get average cost
        avg_cost = get_average_cost(selected_ticker)

        # if average cost is available
        if avg_cost:
            # add a horizontal line for average cost
            fig.add_hline(y=avg_cost, line_width=1, line_dash="dash", line_color="red")

        # show legend on top
        fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

    # show moving average chart
    st.plotly_chart(fig, use_container_width=True)
