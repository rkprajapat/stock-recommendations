import streamlit as st

from utils.utilities import (get_stock_scores, load_portfolio,
                             update_stock_scores)


def app():
    st.title("Fundamentals Update")

    # add a checkbox to analyse portfolio
    if st.checkbox("Update Portfolio"):
        # load portfolio
        portfolio = load_portfolio()

        # list tickers
        tickers = portfolio["ticker"].unique().tolist()

        # create a drop down to select stock and clear screen when its value changes
        selected_ticker = st.selectbox("Select a stock", tickers, key="stock_analysis")
    else:
        # create a text input to enter stock ticker and clear screen when its value changes
        selected_ticker = st.text_input(
            "Enter a stock ticker", key="stock_analysis", max_chars=25
        )

    last_date = None

    # check if selected ticker is not empty
    if selected_ticker:
        # run spinner
        with st.spinner("Loading fundamentals..."):
            # load stock scores
            stock_scores = get_stock_scores(selected_ticker)

            # check if stock scores is not empty
            if stock_scores is None:
                st.error("No fundamentals found for this stock")
                return

            # get last date of stock scores
            last_date = stock_scores["date"].max()

            # show last date
            st.write(f"Last record on {last_date}")

    # wait for last date to be loaded
    if last_date is None:
        return

    # list all fundamentals as input boxes
    fundamentals = {
        "Piotroski F-Score": st.number_input("Piotroski F-Score", format="%.2f"),
    }

    # show a button to update fundamentals
    if st.button("Update"):
        # check if fundamentals values are not empty
        if not fundamentals:
            st.error("Please enter values for fundamentals")
            return

        # update fundamentals
        stock_scores["piotroski_f_score"] = fundamentals["Piotroski F-Score"]

        # update final score
        stock_scores["final_score"] = (
            stock_scores["piotroski_f_score"] + stock_scores["final_score"]
        )

        # save stock scores
        result = update_stock_scores(stock_scores)

        # if result is true, show success message
        if result:
            # show scores
            st.write(stock_scores)
            st.success("Fundamentals updated successfully")

        else:
            st.error("Something went wrong")
    return
