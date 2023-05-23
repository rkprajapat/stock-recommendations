import smtplib
import ssl
from email.message import EmailMessage

import pandas as pd
import streamlit as st

from utils.sell_triggers import compile_sell_triggers
from utils.utilities import run_daily_at_time


def app():
    # add page title
    st.title("Schedule Notifications")

    # add a subheader
    st.subheader("Receiver Emails")

    # add input control to provide multiple emails that become a list
    emails = st.text_input("Enter emails separated by comma", key="emails")

    # validate emails
    if emails:
        # split emails
        emails = emails.split(",")
        # remove whitespaces
        emails = [email.strip() for email in emails]
        # validate emails
        for email in emails:
            # if email is not valid
            if not validate_email(email):
                # show an error message
                st.error(f"Email {email} is not valid.")
                # exit
                return

    # add a selectbox to select the schedule time every day between 4PM to 10PM
    schedule_time = st.selectbox(
        "Select schedule time", [f"{i}:00" for i in range(16, 22)], key="schedule_time"
    )

    # get all notifications with a spinner
    with st.spinner("Loading notifications..."):
        notifications = collect_triggers()

    # show all notifications as tabs
    for notification, content in notifications.items():
        # add a subheader
        st.subheader(notification)
        # show the content
        st.write(content)

    # add a button to send email
    if st.button("Schedule Email"):
        # run a spinner
        with st.spinner("Sending email..."):
            # loop through each notification
            for notification, content in notifications.items():
                # send email
                send_email(emails, notification, content)
                # create a scheduled job
                # run_daily_at_time(send_email, schedule_time, notification, content)


# validate email
def validate_email(email):
    # check if email is valid
    if "@" in email and "." in email:
        # return True
        return True
    # return False
    return False


def collect_triggers():
    # Define notifications
    notifications = {
        # get sell triggers and convert to html table
        "Sell Triggers": compile_sell_triggers(),
    }

    return notifications


# use gmail account to send email
# make sure to enable less secure apps
# https://myaccount.google.com/lesssecureapps
def send_email(receivers, subject, content_generator):
    sender = "Stock Analysis App <roopak.prajapat@gmail.com>"
    password = "Garwal123$"
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    try:
        message = content_generator

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.ehlo()
        server.starttls()
        server.login(sender, password)
        message = f"Subject: {subject}\n\n{message}"
        server.sendmail(sender, receivers, message)

        print("Email sent successfully.")
    except Exception as e:
        print("Error: ", e)
    finally:
        server.quit()
