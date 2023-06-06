import dataclasses
from datetime import date, datetime, time, timedelta

import yfinance as yf

from utils.custom_logger import systemLogger


class Ticker:
    """Class to store ticker data"""

    ticker: str
    date: str
    quantity: int
    price: float
    transaction_type: str

    def __init__(
        self, ticker, date=datetime.today(), quantity=1, price=1, transaction_type="Buy"
    ):
        # check if ticke is already in NS format or not and if not convert it to NS format
        self.ticker = ticker if ticker.endswith(".NS") else f"{ticker}.NS"

        # check if valid ticker
        if not self.is_valid_ticker():
            raise ValueError("Invalid ticker")

        self.date = date
        self.quantity = int(quantity if transaction_type == "Buy" else -quantity)
        self.price = round(price, 2)
        self.transaction_type = transaction_type

    def __repr__(self):
        return f"{self.ticker} {self.date} {self.quantity} {self.price} {self.transaction_type}"

    def __str__(self):
        return f"{self.ticker} {self.date} {self.quantity} {self.price} {self.transaction_type}"

    def __eq__(self, other):
        if (
            self.ticker == other.ticker
            and self.date == other.date
            and self.quantity == other.quantity
            and self.price == other.price
            and self.transaction_type == other.transaction_type
        ):
            return True
        return False

    def __ne__(self, other):
        if (
            self.ticker != other.ticker
            or self.date != other.date
            or self.quantity != other.quantity
            or self.price != other.price
            or self.transaction_type != other.transaction_type
        ):
            return True
        return False

    def __hash__(self):
        return hash(
            (self.ticker, self.date, self.quantity, self.price, self.transaction_type)
        )

    def to_dict(self):
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def is_valid_ticker(self):
        try:
            yf.Ticker(self.ticker).info
            return True
        except:
            systemLogger.error(f"Invalid ticker {self.ticker}")
            return False

    def get_last_price(self) -> tuple:
        """return last price and last price date"""
        price = round(self.get_stock_history().iloc[-1]["Close"], 2)
        price_date = self.get_stock_history().index[-1].strftime("%d-%m-%Y")
        return price, price_date

    @property
    def latest_price(self):
        return yf.Ticker(self.ticker).fast_info['lastPrice']

    def get_last_change(self) -> tuple:
        """return last change and last change percentage

        Returns:
            tuple: change, percent_change
        """
        change = round(
            self.get_stock_history().iloc[-1]["Close"]
            - self.get_stock_history().iloc[-2]["Close"],
            2,
        )
        percent_change = round(
            (change / self.get_stock_history().iloc[-2]["Close"]) * 100, 2
        )
        return change, percent_change

    @property
    def company_name(self):
        return str(yf.Ticker(self.ticker).info["longName"]).capitalize()

    def get_stock_history(self, start=None, end=datetime.today()):
        if start is None:
            start = date.today() - timedelta(days=365 * 2)
        return yf.Ticker(self.ticker).history(start=start, end=end)

    def get_multiplier(self):
        if self.transaction_type == "Buy":
            return 1
        return -1

    def get_total_investment(self):
        return self.quantity * self.price

    def get_current_value(self):
        return self.quantity * self.latest_price

    def get_profit_loss(self):
        return self.get_current_value() - self.get_total_investment()

    def get_profit_loss_percentage(self):
        return (self.get_profit_loss() / self.get_total_investment()) * 100

    def get_average_price(self):
        return self.get_total_investment() / self.quantity

    def get_piotroski_score(self):
        """Calculate Piotroski Score for the stock

        Returns:
            int: Piotroski Score
        """
        score = 0
        financial_data = yf.Ticker(self.ticker).financials

        if financial_data['ROA'] > 0:
            score += 1
        if financial_data['CFO'] > 0:
            score += 1
        if financial_data['DILUTION_RATIO'] < 1:
            score += 1
        if financial_data['ASSET_TURNOVER'] > financial_data['ASSET_TURNOVER'].shift(1):
            score += 1
        if financial_data['CURRENT_RATIO'] > financial_data['CURRENT_RATIO'].shift(1):
            score += 1
        if financial_data['LONG_TERM_DEBT_TO_EQUITY_RATIO'] < financial_data['LONG_TERM_DEBT_TO_EQUITY_RATIO'].shift(1):
            score += 1
        if (financial_data['GROSS_MARGIN'] - financial_data['GROSS_MARGIN'].shift(1)) > 0:
            score += 1
        if financial_data['RETURN_ON_ASSETS'] > financial_data['RETURN_ON_ASSETS'].shift(1):
            score += 1
        return score
