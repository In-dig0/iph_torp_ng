import streamlit as st
import pandas as pd
import sqlite_db
import datetime
import time
from typing import Optional, Tuple, Dict, List
import altair as alt
# Internal app module
import servant

def dashboard(conn):
# Show some metrics and charts about the ticket.
    # st.header("Statistics")

    # # Show metrics side by side using `st.columns` and `st.metric`.
    # col1, col2, col3 = st.columns(3)
    # num_open_requests = len(st.session_state.df_requests[st.session_state.df_requests["STATUS"] == "NEW"])
    # num_assigned_requests = len(st.session_state.df_requests[st.session_state.df_requests["STATUS"] == "ASSIGNED"])
    # num_completed_requests = len(st.session_state.df_requests[st.session_state.df_requests["STATUS"] == "COMPLETED"])
    # col1.metric(label="Number of NEW requests", value=num_open_requests, delta=10)
    # col2.metric(label="Number of ASSIGNED requests", value=num_assigned_requests, delta=-1.5)
    # col3.metric(label="Number of COMPLETED requests", value=num_completed_requests, delta=2)

    # # Show two Altair charts using `st.altair_chart`.
    # st.write("")
    # st.write("##### Requests status per day")
    # status_plot = (
    #     alt.Chart(st.session_state.df_requests)
    #     .mark_bar()
    #     .encode(
    #         x="day(Insdate):O",
    #         y="count():Q",
    #         xOffset="Status:N",
    #         color="Status:N",
    #     )
    #     .configure_legend(
    #         orient="bottom", titleFontSize=14, labelFontSize=14, titlePadding=5
    #     )
    # )
    # st.altair_chart(status_plot, use_container_width=True, theme="streamlit")

    # st.write("##### Current requests procut line")
    # priority_plot = (
    #     alt.Chart(st.session_state.df_requests)
    #     .mark_arc()
    #     .encode(theta="count():Q", color="PR_LINE:N")
    #     .properties(height=300)
    #     .configure_legend(
    #         orient="bottom", titleFontSize=14, labelFontSize=14, titlePadding=5
    #     )
    # )
    # st.altair_chart(priority_plot, use_container_width=True, theme="streamlit")

    # return True

    # Show some metrics and charts about the ticket.
    st.header("Requests Statistics")

    # Show metrics side by side using `st.columns` and `st.metric`.
    col1, col2, col3, col4 = st.columns(4)
    num_open_requests = len(st.session_state.df_requests[st.session_state.df_requests["STATUS"] == "NEW"])
    num_assigned_requests = len(st.session_state.df_requests[st.session_state.df_requests["STATUS"] == "ASSIGNED"])
    num_completed_requests = len(st.session_state.df_requests[st.session_state.df_requests["STATUS"] == "COMPLETED"])
    num_pending_requests = len(st.session_state.df_requests[st.session_state.df_requests["STATUS"] == "PENDING"])


    col1.metric(label="Number of NEW requests", value=num_open_requests, delta=10)
    col2.metric(label="Number of ASSIGNED requests", value=num_assigned_requests, delta=-1.5)
    col3.metric(label="Number of COMPLETED requests", value=num_completed_requests, delta=2)
    col4.metric(label="Number of PENDING requests", value=num_pending_requests, delta=1)

    # Verifichiamo i dati
    #st.write("Preview dei dati:")
    #st.write(st.session_state.df_requests.head())

    #st.write("Colonne disponibili:")
    #st.write(st.session_state.df_requests.columns.tolist())

    # Convertiamo la colonna Insdate in datetime se non lo è già
    st.session_state.df_requests['INSDATE'] = pd.to_datetime(st.session_state.df_requests['INSDATE'])
    st.session_state.df_requests['DATE'] = st.session_state.df_requests['INSDATE'].dt.strftime('%Y-%m-%d')
    st.session_state.df_requests['WEEK_YEAR'] = st.session_state.df_requests['INSDATE'].dt.strftime('%U-%Y')
    # Grafico semplificato
    # status_plot = alt.Chart(st.session_state.df_requests).mark_bar().encode(
    #     x='month(DATE):O',
    #     y='count():Q',
    #     color='PR_LINE:N'
    # )
    
    # Grafico con Altair
    status_plot = alt.Chart(st.session_state.df_requests).mark_bar().encode(
        x=alt.X('WEEK_YEAR:O', title='Week-Year'),
        y=alt.Y('count():Q', title='Count'),
        color=alt.Color('PR_LINE:N', title='Product Line')
    )


    # Proviamo a visualizzare il grafico
    try:
        st.altair_chart(status_plot, use_container_width=True)
    except Exception as e:
        st.error(f"Errore nella visualizzazione del grafico: {str(e)}")

    # Grafico semplificato
    dept_plot = alt.Chart(st.session_state.df_requests).mark_bar().encode(
        x=alt.X('month(DATE):O', title='Month'),
        y=alt.Y('count():Q', title='Count'),
        color=alt.Color('DEPT:N', title='Department')
    )   

    # Proviamo a visualizzare il grafico
    try:
        st.altair_chart(dept_plot, use_container_width=True)
    except Exception as e:
        st.error(f"Errore nella visualizzazione del grafico: {str(e)}")