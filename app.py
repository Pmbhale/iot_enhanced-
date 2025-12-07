import streamlit as st
import login
import dashboard

st.set_page_config(page_title="IoT Monitoring", layout="wide")

# ------------------------
# INITIAL SESSION STATE
# ------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ------------------------
# PAGE CONTROLLER
# ------------------------
if not st.session_state.logged_in:
    login.login_page()
else:
    dashboard.dashboard_page()
