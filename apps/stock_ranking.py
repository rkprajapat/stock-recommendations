import pandas as pd
import streamlit as st
import numpy as np
import time
import humanize

from utils.utilities import (
    calculate_stock_scores,
    get_stock_scores,
    get_stock_watchlist,
    load_portfolio,
    update_stock_scores,
    is_good_buy,
)

from utils.custom_logger import systemLogger


# create a function to get stock scores
def app():
    # set page title
    st.title("Stock Ranking")

    systemLogger.info("Loading Stock Ranks")

    # create force refresh flag
    force_refresh = False

    # if button is clicked, set force refresh to true
    if st.button("Force Refresh"):
        force_refresh = True

    # create a sidebar
    st.sidebar.title("Stock Ranking")

    # show optins to see all stocks or portfolio stocks
    show_all = st.sidebar.checkbox("Show all stocks")

    # if show is not checked, show portfolio stocks
    if not show_all:
        # load portfolio
        systemLogger.info("Loading Portfolio")
        portfolio = load_portfolio()

        # get all tickers
        tickers = portfolio["ticker"].unique().tolist()
    else:
        systemLogger.info("Loading Stock Watchlist")
        # get stock watchlist
        stock_watchlist = get_stock_watchlist()

        # get all tickers
        tickers = stock_watchlist.index.tolist()

    # Create a progress bar with a label
    progress_bar = st.progress(0)
    progress_label = st.empty()
    time_remaining_label = st.empty()
    rank_table = st.dataframe(pd.DataFrame())
    percent_complete = 0

    # create a dataframe to store stock scores
    stock_ranks = pd.DataFrame()

    # create a variable to store total time
    total_time = 0

    # loop through all tickers with an index
    for index, ticker in enumerate(tickers):
        systemLogger.info(f"Retrieving scores for {ticker}")

        # measure start time
        start_time = time.perf_counter()

        # update progress bar
        percent_complete = (index + 1) / len(tickers)

        # show spinner
        progress_label.text(f"Calculating scores for {ticker}... [{percent_complete*100:.2f}%]")

        # calculate average time per ticker
        avg_time_per_ticker = total_time / (index + 1)

        # show time remaining
        time_remaining_label.text(
            f"Time remaining: {humanize.naturaldelta(avg_time_per_ticker * (len(tickers) - index))}"
        )

        # check if good buy
        if show_all and not is_good_buy(ticker):
            systemLogger.info(f"{ticker} is not a good buy")
            continue

        if force_refresh:
            systemLogger.info("Force Refreshing Stock Ranks")
            # disable force refresh button
            st.button("Force Refresh", key="force_refresh", disabled=True)
            
            # calculate stock scores
            stock_score = calculate_stock_scores(ticker)
            update_stock_scores(stock_score)
        else:
            # get stock scores
            systemLogger.info(f"Loading stock scores for {ticker}")
            stock_score = get_stock_scores(ticker)
            

        # if stock score is empty, continue to next ticker
        if stock_score is None or len(stock_score) == 0:
            systemLogger.error(f"No stock scores found for {ticker}")
            continue

        # append stock scores to dataframe using concat
        systemLogger.info(f"Appending stock scores for {ticker}")

        # if stock_ranks is empty, set stock_score as stock_ranks
        if stock_ranks.empty:
            stock_ranks = stock_score
        else:
            # concat stock ranks and stock score
            stock_ranks = pd.concat([stock_ranks, stock_score])

        # sort by latest date and final score
        stock_ranks.sort_values(
            by=["date", "final_score"], ascending=[False, False], inplace=True
        )

        # reorganize columns to show ticker, date and final score first
        stock_ranks = stock_ranks[
            ["ticker", "date", "final_score"]
            + [
                col
                for col in stock_ranks.columns
                if col not in ["ticker", "date", "final_score"]
            ]
        ]

        # reset index
        stock_ranks.reset_index(drop=True, inplace=True)

        # show rank table
        rank_table.dataframe(stock_ranks)

        # update progress bar
        progress_bar.progress(percent_complete)

        # measure total time taken
        total_time += time.perf_counter() - start_time

    # if stock ranks is empty, show message
    if stock_ranks.empty:
        systemLogger.error("No stock scores found")
        progress_label.text("No stock scores found")
        return

    # update progress label with total tickers processed
    progress_label.text(f"Total tickers processed: {len(tickers)}")

    return
