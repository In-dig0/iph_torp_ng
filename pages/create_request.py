# 3th party packages
import streamlit as st
import pandas as pd
# Built-in packages
import datetime
import time
from typing import Optional, Tuple, Dict, List
# Internal app module
import modules.servant 
import modules.sqlite_db

def create_request(conn)-> None:
    """Function to insert a new request"""

    # Add custom CSS for containers
    st.markdown("""
        <style>
        .styledContainer {
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 20px;
            margin-bottom: 20px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Definizione delle chiavi del form
    FORM_KEYS = [
        'sb_dept', 'sb_requester', 'sb_pline', 'sb_pfamily',
        'sb_type', 'sb_category', 'sb_detail', 
        'ti_title', 'ti_description', 'tg_attach'
    ]
    
    # Inizializzazione dello stato del form
    if 'form_submitted' not in st.session_state:
        st.session_state.form_submitted = False
        
    # Inizializzazione delle chiavi del form se non esistono
    for key in FORM_KEYS:
        if key not in st.session_state:
            if key.startswith('sb_'):
                st.session_state[key] = None 
            elif key.startswith('tg_'):
                st.session_state[key] = False
            else:
                st.session_state[key] =""
            
    def reset_form_state():
        """Reset all form fields to their initial state"""
        st.session_state.form_submitted = True
        for key in FORM_KEYS:
            if key in st.session_state:
                del st.session_state[key]
    
    def handle_file_upload():
        """Handle file upload"""
        attachment_list = []
        try:
            uploaded_file = st.file_uploader("Attach PDF file", type=['pdf'], key="pdf_upload_widget")
            if uploaded_file is not None and not isinstance(uploaded_file, str):
                file_content = uploaded_file.read()
                file_name = uploaded_file.name               
                class_type = "PDF"
                link = ""
                attachment = {"class_type":class_type, "title":file_name, "link":link, "file_content": file_content}
                attachment_list.append(attachment)
        except Exception as e:
            st.error(f"Error uploading file: {e}")
            return []
            
        return attachment_list


    def show_request_popup(request_data: dict) -> None:
        """Display confirmation popup after request submission"""
        
        @st.dialog(title=f"Request {request_data['reqid']} submitted!")  
        def show_popup():
            """Form with widgets to collect user information"""
            st.markdown(
                """
                <style>
                div[data-testid="stTextInput"] > div > div > input:not([disabled]) {
                    color: #28a745;
                    border: 2px solid #28a745;
                    -webkit-text-fill-color: #28a745 !important;
                    font-weight: bold;
                }
                div[data-testid="stTextInput"] > div > div > input[disabled] {
                    color: #6c757d !important;
                    opacity: 1 !important;
                    -webkit-text-fill-color: #6c757d !important;
                    background-color: #e9ecef !important;
                    border: 1px solid #ced4da !important;
                    font-style: italic;
                }
                .stSelectbox > div > div > div > div {
                    color: #28a745;
                }
                .stMultiSelect > div > div > div > div {
                    color: #28a745 !important;
                }
                .stMultiSelect div[role="option"] {
                    color: #28a745 !important;
                }
                .stMultiSelect div[role="option"] > div > div {
                    color: #28a745 !important;
                }
                </style>
                """,
                unsafe_allow_html=True
            )          
            
            st.text_input(label=":blue[Request title]", value=request_data["title"], disabled=True)
            req_status_options = ['NEW', 'PENDING', 'ASSIGNED', 'WIP', 'COMPLETED', 'DELETED']
            idx_status = req_status_options.index(request_data["status"])
            st.selectbox(label=":blue[Request status]", options=req_status_options, disabled=True, index=idx_status)

            if st.button("Close"):
                st.session_state.reset_form = True
                time.sleep(0.3)  # Piccola pausa per assicurare il corretto aggiornamento dello stato
                st.rerun()

        return show_popup()


    def show_request_form():
    
        modules.sqlite_db.initialize_session_state(conn)

        # REQUESTER INFO SECTION
        st.subheader(":orange[Requester section]")
        with st.container(border=True):
            # 'Department' selection
            department = st.selectbox(
                label=":blue[Department(:red[*])]", 
                options=st.session_state.df_depts['NAME'].tolist(),
                index=None, 
                key="sb_dept")
            dept_code = modules.servant.get_code_from_name(st.session_state.df_depts, department, "CODE")
            
            # 'Requester' selection
            if department:
                filtered_users = st.session_state.df_users[st.session_state.df_users["DEPTNAME"] == department]
            else:
                filtered_users = st.session_state.df_users

            requester = st.selectbox(
                label=":blue[Requester(:red[*])]", 
                index=None, 
                options=filtered_users["NAME"].tolist(),
                key="sb_requester")
            requester_code = modules.servant.get_code_from_name(st.session_state.df_users, requester, "CODE")

        # PRODUCT INFO SECTION
        st.subheader(":orange[Product section]")
        with st.container(border=True):
           
            # 'Product line' selection
            pline = st.selectbox(
                label=":blue[Product line(:red[*])]", 
                options=st.session_state.df_pline['NAME'].tolist(), 
                index=None,
                key="sb_pline")
            pline_code = modules.servant.get_code_from_name(st.session_state.df_pline, pline, "CODE")

            # 'Product family' selection
            if pline:
                filtered_pfamily = st.session_state.df_pfamily[st.session_state.df_pfamily["PLINE_CODE"] == pline_code]
            else:
                filtered_pfamily = st.session_state.df_pfamily
            
            pfamily = st.selectbox(
                label=":blue[Product family(:red[*])]", 
                options=filtered_pfamily["NAME"].tolist(), 
                index=None,
                key="sb_pfamily")
            pfamily_code = modules.servant.get_code_from_name(st.session_state.df_pfamily, pfamily, "CODE")

        # REQUEST INFO SECTION
        st.subheader(":orange[Request section]")
        with st.container(border=True):
    
            # 'Priority' selection
            priority = st.selectbox(
                label=":blue[Request priorty(:red[*])]", 
                options=["High", "Medium", "Low"], 
                index=1,
                key="sb_priority")    

            # 'Due date' selection
            duedate = st.date_input(
                label=":blue[Desired due date(:red[*])]", 
                value=None,
                format="DD/MM/YYYY",
                key="di_duedate")   

            # 'Type' selection
            reqtype = st.selectbox(
                label=":blue[Request type(:red[*])]", 
                options=st.session_state.df_type['NAME'].tolist(), 
                index=None,
                key="sb_type")
            reqtype_code = modules.servant.get_code_from_name(st.session_state.df_type, reqtype, "CODE")

            # 'Category' selection
            category_filter = st.session_state.df_lk_type_category[st.session_state.df_lk_type_category["TYPE_CODE"] == reqtype_code]
            filtered_reqcategory = st.session_state.df_category[st.session_state.df_category["CODE"].isin(category_filter["CATEGORY_CODE"])]
            
            reqcategory = st.selectbox(
                label=":blue[Request category(:red[*])]", 
                options=filtered_reqcategory["NAME"].tolist(), 
                index=None,
                key="sb_category")
            reqcategory_code = modules.servant.get_code_from_name(st.session_state.df_category, reqcategory, "CODE")

            # 'Detail' selection
            detail_filter = st.session_state.df_lk_category_detail[st.session_state.df_lk_category_detail["CATEGORY_CODE"] == reqcategory_code]
            filtered_detail = st.session_state.df_detail[st.session_state.df_detail["CODE"].isin(detail_filter["DETAIL_CODE"])]
            
            detail = st.selectbox(
                label=":blue[Request detail(:red[*])]", 
                options=filtered_detail["NAME"].tolist(), 
                index=None,
                key="sb_detail")
            detail_code = modules.servant.get_code_from_name(st.session_state.df_detail, detail, "CODE")

            # 'Title' selection
            title = st.text_input(
                label=":blue[Request title(:red[*])]", 
                key="ti_title")

            # 'Description' selection        
            description = st.text_area(
                label=":blue[Request description]", 
                key="ti_description")

            # 'TD Team Leader' selection (hidden)
            tdtl_filter = st.session_state.df_lk_pline_tdtl[st.session_state.df_lk_pline_tdtl["PLINE_CODE"] == pline_code]
            tdtl_option = st.session_state.df_users[st.session_state.df_users["CODE"].isin(tdtl_filter["USER_CODE"])]
            tdtl_code_list = tdtl_option["CODE"].tolist()        

            insdate = datetime.datetime.now().strftime("%Y-%m-%d")
            fix_user = "RB"

        # REQUEST ATTACHMENT SECTION
        st.subheader(":orange[Attachments section]")        
        with st.container(border=True):
            file_upload_on = st.toggle("Activate File upload", key="tg_attach")
            if file_upload_on:
                attachments_list = handle_file_upload()
            else:
                attachments_list = []         
        
        request_info = {
            "insdate": insdate,
            "user": fix_user,
            "status": "NEW",
            "dept": dept_code,
            "requester": requester_code,
            "priority": priority,
            "pline": pline_code,
            "pfamily": pfamily_code,
            "type": reqtype_code,
            "category": reqcategory_code,
            "detail": detail_code,            
            "title": title,
            "description": description,
            "tdtl_list": tdtl_code_list,
            "attachments_list": attachments_list
        }
        
        return request_info

    # Check if we need to reset the form
    if st.session_state.form_submitted:
        reset_form_state()
        st.session_state.form_submitted = False
        st.rerun()

    # Main form handling
    request_data = show_request_form()
    st.divider()
    
    save_button_disabled = not all([
        request_data["dept"], request_data["requester"], 
        request_data["pline"], request_data["pfamily"], 
        request_data["type"], request_data["category"],
        request_data["detail"], request_data["title"]
    ])

    if st.button("Submit", type="primary", disabled=save_button_disabled):
        req_nr, rc = modules.sqlite_db.save_request(request_data, conn)
        if rc:
            request_data["reqid"] = req_nr
            if request_data["attachments_list"]:
                rc = modules.sqlite_db.save_attachments(req_nr, request_data["attachments_list"], conn)
            show_request_popup(request_data)
            #st.success(f"Request {req_nr} submitted successfully!")
            st.session_state.form_submitted = True
            time.sleep(10)  # Piccola pausa per assicurare il corretto aggiornamento dello stato            
            st.rerun()
        else:
            st.error(f"**Error saving request!")        

    return request_data


def main():
    pass

if __name__ == "__main__":
    main()
else:
    create_request(st.session_state.conn)