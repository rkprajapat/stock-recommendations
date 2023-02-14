import streamlit as st

from utils.utilities import get_stock_scores, load_portfolio, update_stock_scores


def app():
    st.title("Fundamentals Update")

    # load portfolio
    portfolio = load_portfolio()

    # get all tickers
    tickers = portfolio["ticker"].unique().tolist()

    # show a drop down to select a ticker
    ticker = st.selectbox("Select a ticker", tickers)

    # list all fundamentals as input boxes
    fundamentals = {
        "Piotroski F-Score": st.number_input(
            "Piotroski F-Score", value=0.0, format="%.2f"
        ),
    }

    # show a button to update fundamentals
    if st.button("Update"):
        # load stock scores
        stock_scores = get_stock_scores(ticker)

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
