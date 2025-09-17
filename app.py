import streamlit as st
import pandas as pd
import joblib
import lightgbm as lgb
from geopy.distance import geodesic
import random

# Load model and encoder
model = joblib.load("fraud_detection_model.jb")
encoder = joblib.load("label_encoder.jb")

def haversine(lat1, lon1, lat2, lon2):
    return geodesic((lat1, lon1), (lat2, lon2)).km

# Initialize CAPTCHA
if 'num1' not in st.session_state or 'num2' not in st.session_state:
    st.session_state.num1 = random.randint(1, 10)
    st.session_state.num2 = random.randint(1, 10)
    st.session_state.captcha_answer = st.session_state.num1 + st.session_state.num2

# Styling
st.markdown("""
    <style>
    body, .stApp {
        background: linear-gradient(120deg, #f6d365 0%, #fda085 100%);
        font-family: Arial, sans-serif;
    }
    .icon {
        font-size: 60px;
        margin-bottom: 10px;
        animation: bounce 1s infinite alternate;
        text-align: center;
    }
    .credit-card-img {
        display: block;
        margin: 0 auto 1rem auto;
        width: 80px;
    }
    .captcha-google {
        border: 1px solid #d3d3d3;
        border-radius: 4px;
        background-color: #fff;
        padding: 10px;
        width: 100%;
        max-width: 320px;
        margin: 0 auto 1rem auto;
        display: flex;
        align-items: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .captcha-checkbox {
        width: 20px;
        height: 20px;
        border: 1px solid #d3d3d3;
        border-radius: 2px;
        margin-right: 10px;
    }
    .captcha-text {
        font-size: 14px;
        color: #3c4043;
    }
    /* Force captcha input + button to stick together */
    div[data-baseweb="numberinput"] {
        margin-bottom: 0px !important;
        padding-bottom: 0px !important;
    }
    div.stButton {
        margin-top: 0px !important;
        padding-top: 0px !important;
    }
    .stButton > button {
        background: linear-gradient(90deg, #43c6ac 0%, #191654 100%);
        color: #fff;
        border-radius: 8px;
        font-weight: bold;
        padding: 0.7rem 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<img src="https://img.icons8.com/ios-filled/100/000000/bank-card-back-side.png" class="credit-card-img" />', unsafe_allow_html=True)
st.markdown('<div class="icon">🔍</div>', unsafe_allow_html=True)
st.markdown('<h1 style="text-align:center;">Fraud Detection System</h1>', unsafe_allow_html=True)
st.write("Enter the Transaction details below")

# Input fields
col1, col2 = st.columns(2)
with col1:
    merchant = st.text_input("Merchant Name")
    category = st.text_input("Category")
    amt = st.number_input("Transaction Amount", min_value=0.0, format="%.2f")
    gender = st.selectbox("Gender", ["Male", "Female"])
    cc_num = st.text_input("Credit Card Number")

    verify = st.checkbox("I'm not a robot")
    if verify:
        user_captcha = st.number_input(
            f"What is {st.session_state.num1} + {st.session_state.num2}?",
            min_value=0, step=1, format="%d"
        )
        # Button placed immediately after captcha
        check_fraud = st.button("Check For Fraud")
    else:
        user_captcha = None
        check_fraud = st.button("Check For Fraud")

with col2:
    lat = st.number_input("Latitude", format="%.6f")
    long = st.number_input("Longitude", format="%.6f")
    merch_lat = st.number_input("Merchant Latitude", format="%.6f")
    merch_long = st.number_input("Merchant Longitude", format="%.6f")
    hour = st.slider("Transaction Hour", 0, 23, 12)
    day = st.slider("Transaction Day", 1, 31, 15)
    month = st.slider("Transaction Month", 1, 12, 6)

distance = haversine(lat, long, merch_lat, merch_long)

# Fraud detection logic
if check_fraud:
    if not verify:
        st.error("❌ Please confirm you are not a robot.")
    elif user_captcha is None or user_captcha != st.session_state.captcha_answer:
        st.error("❌ CAPTCHA answer is incorrect. Please try again.")
    elif not merchant or not category or not cc_num:
        st.error("❌ Please fill all required fields.")
    else:
        input_data = pd.DataFrame([[merchant, category, amt, distance, hour, day, month, gender, cc_num]],
                                  columns=['merchant','category','amt','distance','hour','day','month','gender','cc_num'])

        categorical_col = ['merchant','category','gender']
        for col in categorical_col:
            try:
                input_data[col] = encoder[col].transform(input_data[col])
            except ValueError:
                input_data[col] = -1

        input_data['cc_num'] = input_data['cc_num'].apply(lambda x: hash(x) % (10 ** 2))
        prediction = model.predict(input_data)[0]
        result = "Fraudulent Transaction 🚨" if prediction == 1 else "Legitimate Transaction ✅"

        st.markdown(
            f'<div style="text-align:center; margin-top:2rem;"><span class="icon">{"🚨" if prediction == 1 else "✅"}</span><h2>{result}</h2></div>',
            unsafe_allow_html=True
        )

        if prediction == 1:
            st.warning("Alert: This transaction is likely fraudulent!", icon="🚨")
        else:
            st.success("This transaction appears legitimate.", icon="✅")

        # Reset CAPTCHA
        st.session_state.num1 = random.randint(1, 10)
        st.session_state.num2 = random.randint(1, 10)
        st.session_state.captcha_answer = st.session_state.num1 + st.session_state.num2
