import streamlit as st
from multiapp import MultiApp
from apps import (stock_analysis, view_portfolio, add_stock, send_email)

import os
import sys

root_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)),".."))
if root_path not in sys.path:
	print("Adding root path to sys.path: {}".format(root_path))
	sys.path.insert(0,root_path)


apps = MultiApp()

# show page on full width
st.set_page_config(layout="wide")

# Add all your application here
apps.add_app("Portfolio", view_portfolio.app)
apps.add_app("Add/Update Stock", add_stock.app)
apps.add_app("Stock Analysis", stock_analysis.app)
apps.add_app("Notifications", send_email.app)


# The main app
apps.run()