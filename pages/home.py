# 3th party packages
import streamlit as st
# App modules
import modules.sqlite_db

# Global constants
APPNAME = "TORP" #IPH Technical Office Request POC (Proof Of Concept)
APPCODE = "TORP"
APPVERSION = "0.2"

def dispaly_home_page():
    st.header(f":blue[{APPNAME} Web Application]", divider="grey")
    st.markdown(
        """
        <h3>A simple web application developed to manage <br>
        IPH Technical Office Requests.</h3>
        """,
        unsafe_allow_html=True
        )
    st.markdown(f":grey[Version: {APPVERSION}]")
    st.markdown("Powered with Streamlit :streamlit:")
    st.divider()
    # Open SQLITE Cloud database
    modules.sqlite_db.open_sqlitecloud_db()
    with st.expander("System info", icon=":material/language:"):
        st.markdown(f":streamlit: Streamlit Cloud version {st.__version__}")
        st.markdown(f"⛃ Database SQLITE Cloud version {st.session_state.sqlite_version}")

def main():
    pass

if __name__ == "__main__":
    main()
else:
    dispaly_home_page()