import streamlit as st
from streamlit_option_menu import option_menu
import pages as pg

def main():

    st.set_page_config(
    page_title="TORP WebApp",
    page_icon=":material/local_offer:", 
    layout="wide",
    initial_sidebar_state="auto"
    )

    def login():

        st.header(f":orange[TORP Log in]")
        with st.container(border=True):
            user = st.text_input(label="User", value="user_demo@iph.it", disabled=True)
            password = st.text_input(label="Password", value="torp_demo",type="password", disabled=True)
            role = st.selectbox(label="Choose your role", options=ROLES, placeholder="Choose a role")

            if st.button("Log in"):
                st.session_state.role = role
                st.session_state.user = user
                st.rerun()


    def logout():
        st.session_state.role = None
        st.rerun()


    if "role" not in st.session_state:
        st.session_state.role = None
    
    ROLES = [None, "Requester", "Requester Manager", "TD Team Leader", "TD Specialist", "TD Supervisor", "Admin"]

    role = st.session_state.role

    logout_page = st.Page(
        logout, 
        title="Log out", 
        icon=":material/logout:")
    
    settings = st.Page(
        "settings.py", 
        title="Settings", 
        icon=":material/settings:")
    
    homepage = st.Page(
        "pages/home.py",
        title="Homepage",
        icon="ℹ️",
        #icon=":material/home:",
#        default=(role == "Requester")
        default=True
    )

    create_request = st.Page(
        "pages/create_request.py",
        title="Create Request",
        icon="📄",
        #icon=":material/problem:",
        default=False
    )

    view_request = st.Page(
        "pages/view_request.py",
        title="View Requests",
        icon="🔍",
        #icon=":material/list:",
        default=False
    )

    manage_request = st.Page(
        "pages/manage_request.py",
        title="Manage Request",
        icon="🗂️",
        #icon=":material/bookmark_manager:",
        default=False
    )

    manage_workorder = st.Page(
    "pages/manage_workorder.py",
    title="Manage Work Order",
    icon="📌",
    #icon=":material/order_approve:",
    default=False
    )

    manage_workitem = st.Page(
    "pages/manage_workitem.py",
    title="Manage Work Item",
    icon="🎯",
    #icon=":material/task:",
    default=False
    )

    dashboard_request = st.Page(
    "pages/dashboard_request.py",
    title="Dashboard Requests",
    icon="📉",
    default=False
    )

    account_pages = [logout_page, settings]
    requester_pages = [homepage, create_request, view_request]
    requester_manager_pages = [homepage, view_request, manage_request]
    td_team_leader_pages = [homepage, view_request, manage_request, manage_workorder]
    td_specialist_pages = [homepage, manage_workorder, manage_workitem]


    #st.title(f":blue[TORP WebApp]")
    
    # Add IPH logo to sidebar 
    st.logo("images/logo-iph.png", size="large", icon_image="images/logo-iph.png")
    
    #st.sidebar.image("https://iph.it/wp-content/uploads/2020/02/logo-scritta.png", width=140) 
    
    page_dict = {}
    if st.session_state.role in ["Requester"]:
        page_dict["Requester"] = requester_pages
    elif st.session_state.role in ["TD Team Leader"]:
        page_dict["TD Team Leader"] = td_team_leader_pages
    elif st.session_state.role in ["TD Specialist"]:
        page_dict["TD Specialist"] = td_specialist_pages       

    if len(page_dict) > 0:
        pg = st.navigation({"Account": account_pages} | page_dict)
    else:
        pg = st.navigation([st.Page(login)])

    pg.run()
    
    # # horizontal Menu
    # navbar_h_options = ["Home", "Upload", "Tasks", 'Settings']
    # navbar_h = option_menu(None, options=navbar_h_options, 
    #     icons=['house', 'cloud-upload', "list-task", 'gear'], 
    #     menu_icon="cast", default_index=0, orientation="horizontal"
    #     )
    
    # # vertical Menu (-> sidebar)
    # with st.sidebar:
    #     nb_v_menu = ["Home", "Settings"]
    #     navbar_v = option_menu(menu_title="Side Menu", options=nb_v_menu, 
    #         icons=["house", "gear"], menu_icon="cast", default_index=0, orientation="vertical")
    #     st.write(f"You have selecte option {navbar_v}")


if __name__ == "__main__":
    main()


