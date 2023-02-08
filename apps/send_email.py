import streamlit as st
import pandas as pd

import smtplib
import ssl
from email.message import EmailMessage

def app():
    # add page title
    st.title("Notifications")

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

    # add a subheader
    st.subheader("Email Schedule")

    # add a selectbox to select the schedule time every day between 4PM to 10PM
    schedule_time = st.selectbox("Select schedule time", [f"{i}:00" for i in range(16, 22)], key="schedule_time")

    # add a subheader
    st.subheader("Email Content")

    # add a text area to enter email content
    email_content = st.text_area("Enter email content", key="email_content")

    # add a button to send email
    if st.button("Send Email"):
        # run a spinner
        with st.spinner("Sending email..."):
            # send email
            send_email(emails, email_content, schedule_time)


# validate email
def validate_email(email):
    # check if email is valid
    if "@" in email and "." in email:
        # return True
        return True
    # return False
    return False


# use gmail account to send email
# make sure to enable less secure apps
# https://myaccount.google.com/lesssecureapps
def send_email(ticker, results):
    # get user email
    email = st.session_state.email
    # get user name
    name = st.session_state.name

    # create an email message
    message = EmailMessage()
    # set sender email
    message["From"] = ""
    # set receiver email
    message["To"] = ""
    # set email subject
    message["Subject"] = f"Stock Analysis for {ticker}"
    # set email body
    message.set_content(f"""
    Hi {name},


    Here are the results of the stock analysis for {ticker}:

    {results}

    Regards,
    Stock Analysis App
    """)
    # add an attachment
    message.add_attachment(results, filename=f"{ticker}_analysis.txt")

    # create a secure context
    context = ssl.create_default_context()
    # try to send email
    try:
        # send email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            # login to email server
            server.login("", "")

            # send email
            server.send_message(message)
            # show a success message
            st.success("Email sent successfully!")
    # if email could not be sent
    except Exception as e:
        # show an error message
        st.error(f"Email could not be sent. Please try again later. Error: {e}")