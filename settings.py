import streamlit as st

st.header("Settings")
st.info(f"You are logged in as: {st.session_state.role}.")
st.info(f"You are: {st.session_state.user}.")