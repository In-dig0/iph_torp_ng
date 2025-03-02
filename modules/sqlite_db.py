# 3th party packages
import sqlitecloud
import streamlit as st
import pandas as pd
from streamlit_pdf_viewer import pdf_viewer
# Built-in packages
from datetime import datetime, date
import time
import base64
from typing import Optional, Tuple, Dict, List

# Global constants
ACTIVE_STATUS = "ACTIVE"
DISABLED_STATUS = "DISABLED"
DEFAULT_DEPT_CODE = "DTD"
REQ_STATUS_OPTIONS = ['NEW', 'PENDING', 'ASSIGNED', 'WIP', 'COMPLETED', 'DELETED']

def open_sqlitecloud_db():
    """ Open a connection to SQLITE database"""
    db_link = ""
    db_apikey = ""
    db_name = ""
    # Get database information
    try:
        #Search DB credentials using ST.SECRETS
        db_link = st.secrets["db_credentials"]["SQLITECLOUD_DBLINK"]
        db_apikey = st.secrets["db_credentials"]["SQLITECLOUD_APIKEY"]
        db_name = st.secrets["db_credentials"]["SQLITECLOUD_DBNAME"]
    except Exception as errMsg:
        st.error(f"**ERROR: DB credentials NOT FOUND: \n{errMsg}", icon="🚨")
        rc = False
        
    conn_string = "".join([db_link, db_apikey])

    if 'conn' not in st.session_state:
        try:
            # Connect to SQLite Cloud platform
            conn = sqlitecloud.connect(conn_string)
            cursor = conn.cursor()

            # Open SQLite database
            conn.execute(f"USE DATABASE {db_name}")  

            # Get Sqlite Cloud database version
            cursor.execute("SELECT sqlite_version();")
            #st.success(f"Connect to SQLITE CLOUD version {cursor.fetchone()}")
            sqlite_version = cursor.fetchone()
            #st.write(f"{type(sqlite_version)} - {sqlite_version}" )

            if conn:
                st.session_state.conn = conn
            if sqlite_version:    
                st.session_state.sqlite_version = sqlite_version[0]
            if db_name:
                st.session_state.dbname = db_name

        except Exception as errMsg:
            st.error(f"**ERROR connecting to database: \n{errMsg}", icon="🚨")
            return None
        
        finally: 
            if cursor:
                cursor.close() # Close the cursor in a finally block 
        
        return conn
    else:
        return st.session_state["conn"]


def close_sqlitecloud_db(conn):
    with st.container(border=True):
        try:  
            if conn:
                conn.close() 
        except Exception as errMsg:
            st.error(f"**ERROR closing database connection: \n{errMsg}", icon="🚨")
            return False
        return True    



def load_dept_data(conn):
    """ Load TORP_DEPARTMENTS records into df """ 

    try:
        df_depts = pd.read_sql_query("""
            SELECT 
                A.code AS CODE, 
                A.name AS NAME, 
                A.mngrcode AS MNGR_CODE, 
                A.rprofcode AS REQPROF_CODE 
            FROM TORP_DEPARTMENTS AS A
            ORDER by name
            """, conn)
    except Exception as errMsg:
        st.error(f"**ERROR loading data from TORP_DEPARTMENTS: \n{errMsg}", icon="🚨")
        return None
    
    return df_depts

def load_users_data(conn):
    """ Load TORP_USERS records into df """ 

    try:
        df_users = pd.read_sql_query("""
            SELECT 
                A.code AS CODE, 
                A.name AS NAME, 
                A.deptcode AS DEPTCODE,
                A.email AS EMAIL, 
                B.name AS DEPTNAME
            FROM TORP_USERS A
            INNER JOIN TORP_DEPARTMENTS B ON B.code = A.deptcode
            ORDER by A.name
            """, conn)
    except Exception as errMsg:
        st.error(f"**ERROR loading data from TORP_USERS: \n{errMsg}", icon="🚨")
        return None
    
    return df_users

def load_pline_data(conn):
    """ Load TORP_PLINE records into df """ 
    
    try:
        df_pline = pd.read_sql_query("""
            SELECT 
                A.code AS CODE, 
                A.name AS NAME
            FROM TORP_PLINE A
            ORDER by A.name
            """, conn)
    except Exception as errMsg:
        st.error(f"**ERROR loading data from TORP_PLINE: \n{errMsg}", icon="🚨")
        return None
    
    return df_pline

def load_pfamily_data(conn):
    """ Load TORP_PFAMILY records into df """ 

    try:
        df_pfamily = pd.read_sql_query("""
            SELECT 
                A.code AS CODE, 
                A.name AS NAME, 
                A.pcode AS PLINE_CODE
            FROM TORP_PFAMILY A
            ORDER by A.name
            """, conn)
    except Exception as errMsg:
        st.error(f"**ERROR loading data from TORP_PFAMILY: \n{errMsg}", icon="🚨")
        return None
    
    return df_pfamily

def load_type_data(conn):
    """ Load TORP_TYPE records into df """ 

    try:
        df_type = pd.read_sql_query("""
            SELECT 
                A.code AS CODE, 
                A.name AS NAME
            FROM TORP_TYPE A
            ORDER by A.name
            """, conn)
    except Exception as errMsg:
        st.error(f"**ERROR loading data from TORP_TYPE: \n{errMsg}", icon="🚨")
        return None
    
    return df_type

def load_category_data(conn):
    """ Load TORP_CATEGORY records into df """ 

    try:
        df_category= pd.read_sql_query("""
            SELECT 
                A.code AS CODE, 
                A.name AS NAME
            FROM TORP_CATEGORY A
            ORDER by A.name
            """, conn)
    except Exception as errMsg:
        st.error(f"**ERROR loading data from TORP_CATEGORY: \n{errMsg}", icon="🚨")
        return None
    
    return df_category

def load_detail_data(conn):
    """ Load TORP_DETAIL records into df """ 

    try:
        df_detail= pd.read_sql_query("""
            SELECT 
                A.code AS CODE,                                    
                A.name AS NAME
            FROM TORP_DETAIL A
            ORDER by A.name
            """, conn)
    except Exception as errMsg:
        st.error(f"**ERROR loading data from TORP_DETAIL: \n{errMsg}", icon="🚨")
        return None
    
    return df_detail


def load_lk_type_category_data(conn):
    """ Load TORP_LINK_TYPE_CATEGORY records into df """ 

    try:
        df_lk_type_category= pd.read_sql_query("""
            SELECT 
                A.typecode AS TYPE_CODE, 
                A.categorycode AS CATEGORY_CODE
            FROM TORP_LINK_TYPE_CATEGORY A
            ORDER by A.typecode 
            """, conn)
    except Exception as errMsg:
        st.error(f"**ERROR loading data from TORP_LINK_TYPE_CATEGORY: \n{errMsg}", icon="🚨")
        return None
    
    return df_lk_type_category

def load_lk_category_detail_data(conn):
    """ Load TORP_LINK_CATEGORY_DETAIL records into df """ 

    try: 
        df_lk_category_detail= pd.read_sql_query("""
            SELECT 
                A.categorycode AS CATEGORY_CODE, 
                A.detailcode AS DETAIL_CODE
            FROM TORP_LINK_CATEGORY_DETAIL A
            ORDER by A.categorycode 
            """, conn)
    except Exception as errMsg:
        st.error(f"**ERROR loading data from TORP_LINK_CATEGORY_DETAIL: \n{errMsg}", icon="🚨")
        return None
    
    return df_lk_category_detail

def load_lk_pline_tdtl_data(conn):
    """ Load TORP_LINK_PLINE_TDTL records into df """ 

    try:
        df_lk_pline_tdtl= pd.read_sql_query("""
            SELECT 
                A.plinecode AS PLINE_CODE, 
                A.usercode AS USER_CODE
            FROM TORP_LINK_PLINE_TDTL A
            ORDER by A.plinecode 
            """, conn)
    except Exception as errMsg:
        st.error(f"**ERROR loading data from TORP_LINK_PLINE_TDTL: \n{errMsg}", icon="🚨")
        return None
    
    return df_lk_pline_tdtl


def load_tskgrl1_data(conn):
    """ Load TORP_TASKGRP_L1 records into df """ 
    
    try: 
        df_tskgrl1 = pd.read_sql_query("""
            SELECT 
                A.code AS CODE, 
                A.name AS NAME
            FROM TORP_TASKGRP_L1 AS A
            ORDER by name
            """, conn)
    except Exception as errMsg:
        st.error(f"**ERROR load data from TORP_TASKGRP_L1: \n{errMsg}", icon="🚨")
        return None
    
    return df_tskgrl1

def load_tskgrl2_data(conn):
    """ Load TORP_TASKGRP_L2 records into df """    
    
    try:
        df_tskgrl2 = pd.read_sql_query("""
            SELECT 
                A.code AS CODE, 
                A.name AS NAME,
                A.pcode AS PCODE
            FROM TORP_TASKGRP_L2 AS A
            ORDER by name
            """, conn)
    except Exception as errMsg:
        st.error(f"**ERROR load data from TORP_TASKGRP_L2: \n{errMsg}", icon="🚨")
        return None
    
    return df_tskgrl2


def load_permission_data(conn):
    """ Load TORP_PERMISSION records into df """    
    
    try:
        df_permission = pd.read_sql_query("""
            SELECT 
                A.obj AS OBJ, 
                A.rolecode AS ROLECODE,
                A.action AS ACTION
            FROM TORP_PERMISSION AS A
            ORDER by obj
            """, conn)
    except Exception as errMsg:
        st.error(f"**ERROR load data from TORP_PERMISSION: \n{errMsg}", icon="🚨")
        return None
    
    return df_permission


def load_wo_phases_data(conn):
    """ Load TORP_WO_PHASES records into df """    
    
    try:
        df_wo_phases = pd.read_sql_query("""
            SELECT 
                A.woid AS WOID, 
                A.tdtlid AS TDTLID,
                A.phase_code AS PHASE_CODE,
                A.status AS STATUS,
                A.startdate AS STARTDATE,
                A.enddate AS ENDDATE,
                A.progress AS PROGRESS
            FROM TORP_WO_PHASES AS A
            ORDER by woid
            """, conn)
    except Exception as errMsg:
        st.error(f"**ERROR load data from TORP_WO_PHASES: \n{errMsg}", icon="🚨")
        return None
    
    return df_wo_phases


def load_wo_activity_data(conn):
    """ Load TORP_WO_ACTIVITY records into df """    
    
    try:
        df_wo_activity = pd.read_sql_query("""
            SELECT 
                A.rowid AS ROWID,
                A.woid AS WOID, 
                A.tdtlid AS TDTLID,
                A.actgrp_l1 AS ACTGRP_L1,
                A.actgrp_l2 AS ACTGRP_L2,                
                A.status AS STATUS,
                A.startdate AS STARTDATE,
                A.enddate AS ENDDATE,
                A.progress AS PROGRESS,
                A.description AS DESCRIPTION
            FROM TORP_WORKACTIVITY AS A
            ORDER by woid
            """, conn)
    except Exception as errMsg:
        st.error(f"**ERROR load data from TORP_WOACTIVITY: \n{errMsg}", icon="🚨")
        return None
    
    return df_wo_activity


def load_requests_data(conn):
    """ Load TORP_REQUESTS records into df """    

    try:
        df_requests = pd.read_sql_query("""
        SELECT 
            A.reqid AS REQID, 
            A.status AS STATUS, 
            A.insdate AS INSDATE,
            A.duedate AS DUEDATE,                             
            A.dept AS DEPT, 
            A.requester AS REQUESTER, 
            A.user AS USER, 
            A.priority AS PRIORITY, 
            A.pline AS PR_LINE, 
            A.pfamily AS PR_FAMILY, 
            A.type AS TYPE, 
            A.category AS CATEGORY, 
            A.detail AS DETAIL, 
            A.title AS TITLE, 
            A.description AS DESCRIPTION, 
            A.note_td AS NOTE_TD,
            A.duedate_td AS DUEDATE_TD,                             
            A.woid AS WOID  
        FROM TORP_REQUESTS A
        ORDER by REQID desc
        """, conn)
        df_requests["INSDATE"] = pd.to_datetime(df_requests["INSDATE"])
        df_requests["INSDATE"] = df_requests["INSDATE"].dt.strftime('%Y-%m-%d')
        df_requests["DUEDATE"] = pd.to_datetime(df_requests["DUEDATE"])
        df_requests["DUEDATE"] = df_requests["DUEDATE"].dt.strftime('%Y-%m-%d')
        df_requests["DUEDATE_TD"] = pd.to_datetime(df_requests["DUEDATE_TD"])
        df_requests["DUEDATE_TD"] = df_requests["DUEDATE_TD"].dt.strftime('%Y-%m-%d')                  
    except Exception as errMsg:
        st.error(f"**ERROR load data from TORP_REQUESTS: \n{errMsg}", icon="🚨")
        return None
    
    return df_requests

def load_reqassignedto_data(conn):
    """ Load TORP_REQASSIGNEDTO records into df """    

    try:
        df_reqassignedto = pd.read_sql_query("""
        SELECT 
            A.reqid AS REQID,
            A.tdtlid AS TDTLID, 
            A.status AS STATUS,
            B.name AS USERNAME 
        FROM TORP_REQASSIGNEDTO A
        INNER JOIN TORP_USERS B ON B.code = A.tdtlid
        WHERE A.status = 'ACTIVE'
        ORDER BY REQID desc
        """, conn)
    except Exception as errMsg:
        st.error(f"**ERROR load data from TORP_REQASSIGNEDTO: \n{errMsg}", icon="🚨")
        return None
    
    return df_reqassignedto


def load_attachments_data(conn):
    """ Load TORP_ATTACHMENTS records into df """    

    try:
        df_attachments = pd.read_sql_query("""
        SELECT 
            A.class AS CLASS,
            A.title AS TITLE,                                  
            A.reqid AS REQID
        FROM TORP_ATTACHMENTS A
        ORDER BY A.title
        """, conn)
    except Exception as errMsg:
        st.error(f"**ERROR load data from TORP_ATTACHMENTS: \n{errMsg}", icon="🚨")
        return None
    
    return df_attachments


def load_workorders_data(conn):
    """ Load TORP_WORKORDERS records into df """

    try:
        df_workorders = pd.read_sql_query("""
        SELECT 
            A.woid AS WOID,
            A.insdate AS INSDATE,
            A.tdtlid AS TDTLID, 
            A.type AS TYPE, 
            A.status AS STATUS, 
            A.sequence AS SEQUENCE,       
            A.title AS TITLE,
            A.description AS DESCRIPTION,
            A.time_qty AS TIME_QTY,
            A.time_um AS TIME_UM,                                                                
            A.startdate AS STARTDATE, 
            A.enddate AS ENDDATE,                                       
            A.reqid AS REQID,
            A.proj_class AS PROJ_CLASS
        FROM TORP_WORKORDERS A
        ORDER BY REQID
        """, conn)
        df_workorders["INSDATE"] = pd.to_datetime(df_workorders["INSDATE"])
        df_workorders["INSDATE"] = df_workorders["INSDATE"].dt.strftime('%Y-%m-%d')
    except Exception as errMsg:
        st.error(f"**ERROR load data from TORP_WORKORDERS: \n{errMsg}", icon="🚨")
        return None
    return df_workorders

def load_woassignedto_data(conn):
    """ Load TORP_WOASSIGNEDTO records into df """
       
    try:
        df_woassignedto = pd.read_sql_query("""
        SELECT 
            A.woid AS WOID, 
            A.tdtlid AS TDTLID,
            A.tdspid AS TDSPID,
            A.status AS STATUS, 
            B.name AS USERNAME 
        FROM TORP_WOASSIGNEDTO A
        INNER JOIN TORP_USERS B ON B.code = A.tdtlid    
        WHERE A.status = 'ACTIVE'
        OR A.status = 'DISABLED'
        ORDER BY WOID
        """, conn)    
    except Exception as errMsg:
        st.error(f"**ERROR load data from TORP_WOASSIGNEDTO: \n{errMsg}", icon="🚨")
        return None
    return df_woassignedto


def load_workitems_data(conn):
    """ Load TORP_TORP_WORKITEMS records into df """
       
    try:
        df_workitem = pd.read_sql_query("""
        SELECT 
            A.refdate AS REFDATE, 
            A.woid AS WOID, 
            A.tdspid AS TDSPID,
            A.status AS STATUS, 
            A.tskgrl1 AS TSKGRL1,
            A.tskgrl2 AS TSKGRL2,
            A.description AS DESC,
            A.note AS NOTE,
            A.time_qty AS TIME_QTY,
            A.time_um AS TIME_UM
        FROM TORP_WORKITEMS A  
        ORDER BY WOID
        """, conn)
        df_workitem['REFDATE'] = pd.to_datetime(df_workitem['REFDATE'])
        df_workitem["REFDATE"] = df_workitem["REFDATE"].dt.strftime('%Y-%m-%d')            
    except Exception as errMsg:
        st.error(f"**ERROR load data from TORP_WORKITEMS: \n{errMsg}", icon="🚨")
        return None
    return df_workitem


def get_next_object_id(obj_class, obj_year, obj_pline, obj_parent, conn) -> str:
    """Get next available row ID"""

    ZERO_PADDING_NR = 4
    SEP_CHAR = '-'
    WO_PREFIX = "W"
    next_rowid = ""

    # Work Order numeration-> Prefix + numeration of Request
    if obj_class == "WOR": 
        next_rowid = WO_PREFIX + obj_parent[1:]
    
    # Request numeration
    if obj_class == "REQ":    
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT prefix AS PREFIX, prog AS PROG FROM TORP_OBJNUMERATOR WHERE obj_class=? and obj_year=? and obj_pline=?', (obj_class, obj_year, obj_pline))
            results = cursor.fetchone()
            if results:
                prefix = results[0]
                next_prog = int(results[1]) + 1
                next_rowid = prefix + obj_year[2:4] + SEP_CHAR + str(next_prog).zfill(ZERO_PADDING_NR)
                cursor.execute(
                    "UPDATE TORP_OBJNUMERATOR SET prog = ? WHERE obj_class=? and obj_year=? and obj_pline=?",
                    (next_prog, obj_class, obj_year, obj_pline)
                )               
            else:        
                prefix = obj_class[0]
                next_prog = 1
                next_rowid = prefix + obj_year[2:4] + SEP_CHAR + str(next_prog).zfill(ZERO_PADDING_NR)
                cursor.execute(
                    "INSERT INTO TORP_OBJNUMERATOR (obj_class, obj_year, obj_pline, prefix, prog) VALUES (?, ?, ?, ?, ?)",
                    (obj_class, obj_year, obj_pline, prefix, next_prog)
                )

            conn.commit()                        
        except Exception as errMsg:
            st.error(f"**ERROR impossible to get the next rowid from table TORP_OBJNUMERATOR: {errMsg}")
            conn.rollback()
            return ""
        finally:
            if cursor:
                cursor.close() # Close the cursor in a finally block
    
    else:
        st.error(f"**ERROR impossible to get the next rowid for object {obj_class}-{obj_year}-{obj_pline}")
        return ""
    
    return next_rowid


def save_request(request: dict, conn) -> Tuple[str, int]:
    """Save request to database and return request number and status"""

    try:
        cursor = conn.cursor()
        req_year = request["insdate"][0:4]
        next_reqid = get_next_object_id("REQ", req_year, "", "", conn)
        sql = """
            INSERT INTO TORP_REQUESTS (
                reqid, status, insdate, dept, requester, user, 
                priority, pline, pfamily, type, category, detail,
                title, description, note_td, woid
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        values = (
            next_reqid, request["status"], request["insdate"], request["dept"],
            request["requester"], request["user"], request["priority"], 
            request["pline"], request["pfamily"], request["type"], request["category"],
            request["detail"], request["title"], request["description"], "", "" 
        )
        
        cursor.execute(sql, values)
        conn.commit()
        
    except Exception as e:
        st.error(f"**ERROR inserting request in TORP_REQUESTS: \n{e}", icon="🚨")
        return "", False

    try:               
        for tdtl in request["tdtl_list"]: 
            sql = """
                INSERT INTO TORP_REQASSIGNEDTO (
                    reqid, tdtlid, status
                ) VALUES (?, ?, ?)
            """
            values = (
                next_reqid, tdtl, "ACTIVE"

            )
        
        cursor.execute(sql, values)
        conn.commit()
                    
    except Exception as e:
        conn.rollback()
        st.error(f"**ERROR inserting request in TORP_REQASSIGNEDTO: \n{e}", icon="🚨")
        return "", False
    
    finally:
        if cursor:
            cursor.close()  
    
    return next_reqid, True 


# def load_attachments_from_db(reqid: str, conn):
#     """Visualizza gli allegati PDF."""

#     try:
#         cursor = conn.cursor()

#         sql = """
#             SELECT title, data 
#             FROM TORP_ATTACHMENTS 
#             WHERE reqid = :1 
#         """
#         cursor.execute(sql, [reqid])
#         attachments = cursor.fetchall()

#         if not attachments:
#             st.info(f"Nessun allegato trovato per la richiesta {reqid}")
#             return

#         for title, pdf_data in attachments:
#             if pdf_data:
#                 #st.subheader(title)
#                 with st.expander(title):  # Expander per ogni allegato
#                     st.download_button(
#                         label=f" Download PDF - {title}",
#                         data=pdf_data,
#                         file_name=f"{title}.pdf",
#                         mime="application/pdf"
#                     )
#                     # Visualizzazione PDF (con controllo visibilità)
#                     if st.checkbox("Mostra anteprima", key=f"preview_{title}"): # Checkbox univoco per ogni anteprima
#                         base64_pdf = base64.b64encode(pdf_data).decode('utf-8')
#                         pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000"></iframe>'
#                         st.markdown(pdf_display, unsafe_allow_html=True)

#     except Exception as e:
#         st.error(f"Errore nel caricamento degli allegati: {e}")
#         import traceback
#         st.error(traceback.format_exc())
#     finally:
#         if cursor:
#             cursor.close() # Close the cursor in a finally block
#     return True


def save_attachments(req_id: str, attachments_list: list, conn) -> bool:
    """ Salva i file allegati di una richiesta nella tabella TORP_ATTACHMENTS """
    try:
        cursor = conn.cursor()
        for attachments in attachments_list:
            sql = """
                INSERT INTO TORP_ATTACHMENTS (class, title, link, data, reqid)
                VALUES (?, ?, ?, ?, ?)
            """
            cursor.execute(sql, (attachments["class_type"], attachments["title"], attachments["link"], attachments["file_content"], req_id))
            conn.commit()  # Commit AFTER saving
    
    except Exception as e:
        st.error(f"Error saving attachment: {e}")
        conn.rollback() # Rollback on error
        return False
    
    finally:
        if cursor:
            cursor.close() # Close the cursor in a finally block
    
    return True        

# def view_attachments(reqid: str, conn)-> None:
#     """Visualizza gli allegati PDF."""

#     try:
#         with conn:  # Use a context manager for the connection
#             cursor = conn.cursor()

#             sql = """
#                 SELECT title, data 
#                 FROM TORP_ATTACHMENTS 
#                 WHERE reqid = :1 
#             """
#             cursor.execute(sql, [reqid])
#             attachments = cursor.fetchall()

#             if not attachments:
#                 st.info(f"Nessun allegato trovato per la richiesta {reqid}")
#                 return

#             for title, pdf_data in attachments:
#                 if pdf_data:
#                     file_name = f"{reqid}_details.pdf"
#                     with st.expander(title):  # Expander per ogni allegato
#                         st.download_button(
#                             label=f"Download PDF",
#                             data=pdf_data,
#                             file_name=file_name,
#                             mime="application/pdf",
#                             type="primary",
#                             icon=":material/download:"
#                         )
#                         if st.checkbox("Mostra anteprima", key=f"preview_{title}"):  # Checkbox univoco per ogni anteprima
#                             base64_pdf = base64.b64encode(pdf_data).decode('utf-8')
#                             st.write(f"Base64 PDF: {base64_pdf[:100]}...")  # Stampa i primi 100 caratteri
#                             pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000"></iframe>'
#                             st.markdown(pdf_display, unsafe_allow_html=True)
#                             #Debug: Salva il PDF localmente
#                             with open("debug_pdf.pdf", "wb") as f:
#                                 f.write(pdf_data)
                            
#     except Exception as e:
#         st.error(f"Errore nel caricamento degli allegati: {e}")
#         import traceback
#         st.error(traceback.format_exc())
#         return False
#     finally:
#         if cursor:
#             cursor.close() # Close the cursor in a finally block
#     return True

    # Database update functions

def view_attachments(reqid: str, conn) -> None:
    """Visualizza gli allegati PDF."""
    try:
        with conn:
            cursor = conn.cursor()
            sql = "SELECT title, data FROM TORP_ATTACHMENTS WHERE reqid = :1"
            cursor.execute(sql, [reqid])
            attachments = cursor.fetchall()

            if not attachments:
                st.info(f"Nessun allegato trovato per la richiesta {reqid}")
                return

            for title, pdf_data in attachments:
                if pdf_data:
                    file_name = f"{reqid}_details.pdf"
                    with st.expander(title):
                        st.download_button(
                            label="Download PDF",
                            data=pdf_data,
                            file_name=file_name,
                            mime="application/pdf",
                            type="primary",
                            icon=":material/download:"
                        )
                        
                        if st.checkbox("Mostra anteprima", key=f"preview_{title}"):
                            try:
                                # Salva temporaneamente il PDF
                                temp_path = f"temp_{file_name}"
                                with open(temp_path, "wb") as f:
                                    f.write(pdf_data)
                                
                                # Usa il viewer PDF
                                pdf_viewer(temp_path)
                                
                                # Rimuovi il file temporaneo
                                import os
                                os.remove(temp_path)
                                
                            except Exception as e:
                                st.error(f"Errore nella visualizzazione del PDF: {e}")

    except Exception as e:
        st.error(f"Errore nel caricamento degli allegati: {e}")
        import traceback
        st.error(traceback.format_exc())
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
    return True


def update_request(reqid: str, new_status: str, new_note_td: str, new_woid: str, new_tdtl: list, new_duedate_td: str, conn):
    
    #st.write(f"POINT_U0: reqid = {reqid} - new_status = {new_status} - new_note_td = {new_note_td} - new_tdtl = {new_tdtl}")

    if isinstance(new_status, pd.Series):  # Check if it's a Series
        new_status = new_status.iloc[0]
    if isinstance(new_note_td, pd.Series):
        new_note_td = new_note_td.iloc[0]
    if isinstance(new_woid, pd.Series):
        new_woid = new_woid.iloc[0]
    if isinstance(new_duedate_td, pd.Series):
        new_duedate_td = new_duedate_td.iloc[0]        

    # Update TORP_REQUESTS
    try:
        with conn:  # Use a context manager for the connection
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE TORP_REQUESTS SET status = ?, note_td = ?, woid = ?, duedate_td = ? WHERE reqid = ?",
                (new_status, new_note_td, new_woid, new_duedate_td, reqid)
            )
            conn.commit()
    except Exception as e:
        conn.rollback()
        st.error(f"Error updating TORP_REQUESTS: {str(e)}", icon="🚨")
        return False

    # Update TORP_REQASSIGNEDTO
    try:
        if new_tdtl: # Check if the list is not empty
        # 1. Disable existing assignments (important to do this *before* inserting new ones)
            with conn:  # Use a context manager for the connection
                cursor.execute("UPDATE TORP_REQASSIGNEDTO SET status = ? WHERE reqid = ?", (DISABLED_STATUS, reqid))
                conn.commit()
            # 2. Insert new assignments
                for tdtl in new_tdtl:
                    try:
                        # Check if the record already exists in the table
                        cursor.execute("SELECT 1 FROM TORP_REQASSIGNEDTO WHERE reqid = ? AND tdtlid = ?", (reqid, tdtl))
                        existing_record = cursor.fetchone()
                        if existing_record:
                            # Update the existing record
                            cursor.execute("UPDATE TORP_REQASSIGNEDTO SET status = ? WHERE reqid = ? AND tdtlid = ?", (ACTIVE_STATUS, reqid, tdtl))
                        else:
                            # Insert a new record
                            cursor.execute("INSERT INTO TORP_REQASSIGNEDTO (reqid, tdtlid, status) VALUES (?, ?, ?)", (reqid, tdtl, ACTIVE_STATUS))
                        conn.commit()
                    except Exception as e:
                        conn.rollback()
                        st.error(f"Error inserting/updating REQASSIGNEDTO for {tdtl}: {str(e)}", icon="🚨")
                        return False
        else:
            st.warning("Nessun Team Leader fornito per l'aggiornamento di REQASSIGNEDTO", icon="⚠️")

    except Exception as e:
        conn.rollback()
        st.error(f"Error updating REQASSIGNEDTO (disabling): {str(e)}", icon="🚨")
        return False

    finally:
        if cursor:
            cursor.close() # Close the cursor in a finally block
    
    return True


def save_workorder(wo: dict, conn): # Pass connection and cursor
    
    try:
        with conn:
            cursor = conn.cursor()
            # Check if a workorder with the given woid already exists
            cursor.execute("SELECT 1 FROM TORP_WORKORDERS WHERE woid = ? AND tdtlid = ?", (wo["woid"], wo["tdtlid"]))
            existing_workorder = cursor.fetchone()

            if existing_workorder:
                # UPDATE
                sql = """
                    UPDATE TORP_WORKORDERS SET
                        type = ?, 
                        title = ?, 
                        description = ?,
                        time_qty = ?, 
                        time_um = ?, 
                        status = ?, 
                        startdate = ?,
                        enddate = ?, 
                        reqid = ?, 
                        sequence = ?,
                        proj_class = ?
                    WHERE woid = ?
                    AND tdtlid = ?
                """
                values = (
                    wo["type"], 
                    wo["title"], 
                    wo["description"],
                    wo["time_qty"], 
                    wo["time_um"], 
                    wo["status"], 
                    wo["startdate"],
                    wo["enddate"], 
                    wo["reqid"], 
                    wo["sequence"],
                    wo["proj_class"],                    
                    wo["woid"], 
                    wo["tdtlid"]
                )
                cursor.execute(sql, values)
                conn.commit()
                #st.success(f"Workorder {wo['woid']} updated successfully.") # feedback for the user

            else:
                # INSERT
                sql = """
                    INSERT INTO TORP_WORKORDERS (
                        woid, tdtlid, type, title, description, time_qty, time_um,
                        status, startdate, enddate, reqid, insdate, sequence, proj_class
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                values = (
                    wo["woid"], 
                    wo["tdtlid"], 
                    wo["type"], 
                    wo["title"], 
                    wo["description"],
                    wo["time_qty"], 
                    wo["time_um"], 
                    wo["status"], 
                    wo["startdate"],
                    wo["enddate"], 
                    wo["reqid"], 
                    wo["insdate"], 
                    wo["sequence"],
                    wo["proj_class"]
                )
                cursor.execute(sql, values)
                conn.commit()
                #st.success(f"Workorder {wo['woid']} created successfully.") # feedback for the user

    except Exception as e:
        conn.rollback() # important to rollback in case of error!
        st.error(f"**ERROR saving workorder: \n{e}", icon="🚨")
        return "", False

    finally:
        if cursor:
            cursor.close() # Close the cursor in a finally block

    return wo["woid"], True

def save_workorder_assignments(woid, tdtl_code, assigned_users, df_users, df_woassignedto, conn):
    try:
        # Disable existing assignments
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE TORP_WOASSIGNEDTO SET status = ? WHERE woid = ? AND tdtlid = ?",
                (DISABLED_STATUS, woid, tdtl_code)
            )
            conn.commit()
            
            # Add new assignments
            for user_name in assigned_users:
                user_code = df_users[df_users["NAME"] == user_name]["CODE"].iloc[0]
                #st.write(f"{woid} - {tdtl_code} - {user_code} -")

                existing_assignment = df_woassignedto[
                    (df_woassignedto['WOID'] == woid) & 
                    (df_woassignedto['TDTLID'] == tdtl_code) &
                    df_woassignedto['TDSPID'].isin([user_code])
                  ]  # Usa isin()
                
                if existing_assignment.empty:
                    cursor.execute(
                        "INSERT INTO TORP_WOASSIGNEDTO (woid, tdtlid, tdspid, status) VALUES (?, ?, ?, ?)",
                        (woid, tdtl_code, user_code, ACTIVE_STATUS)
                    )
                else:
                    cursor.execute(
                        "UPDATE TORP_WOASSIGNEDTO SET status = ? WHERE woid = ? AND tdtlid = ? AND tdspid = ?",
                        (ACTIVE_STATUS, woid, tdtl_code, user_code)
                    )
            
                conn.commit()
            return True
    
    except Exception as e:
        st.error(f"Error updating TORP_WOASSIGNEDTO: {str(e)}", icon="🚨")
        conn.rollback()
        return False
    
    finally:
        if cursor:
            cursor.close() # Close the cursor in a finally block


def save_workitem(witem: dict, conn) ->  bool:
    """Save request to database and return request number and status"""
    try:
        with conn:
            cursor = conn.cursor()        
            # Check if a workorder with the given woid already exists
            cursor.execute("SELECT 1 FROM TORP_WORKITEMS WHERE refdate = ? AND woid = ? AND tdspid = ?", (witem["REFDATE"], witem["WOID"], witem["TDSPID"]))
            existing_workorder = cursor.fetchone()

            if existing_workorder:
                # UPDATE
                sql = """
                UPDATE TORP_WORKITEMS SET
                    status = ?, 
                    tskgrl1 = ?, 
                    tskgrl2 = ?, 
                    time_qty = ?, 
                    description = ?, 
                    note = ?
                WHERE refdate = ?
                AND woid = ?
                AND tdspid = ?
                """
                values = (
                    witem["STATUS"], 
                    witem["TSKGRL1"], 
                    witem["TSKGRL2"],
                    witem["TIME_QTY"], 
                    witem["DESCRIPTION"],
                    witem["NOTE"],
                    witem["REFDATE"] , 
                    witem["WOID"], 
                    witem["TDSPID"]
                )
                cursor.execute(sql, values)
                conn.commit()
                return True                  

            else:
                sql = """
                    INSERT INTO TORP_WORKITEMS (
                        refdate, 
                        woid, 
                        tdspid, 
                        status, 
                        tskgrl1, 
                        tskgrl2, 
                        description, 
                        note, 
                        time_qty, 
                        time_um
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                values = (
                    witem["REFDATE"], 
                    witem["WOID"], 
                    witem["TDSPID"], 
                    witem["STATUS"],
                    witem["TSKGRL1"], 
                    witem["TSKGRL2"], 
                    witem["DESCRIPTION"], 
                    witem["NOTE"], 
                    witem["TIME_QTY"], 
                    witem["TIME_UM"]
                )
                cursor.execute(sql, values)
                conn.commit()
                return True
    
    except Exception as e:
        st.error(f"**ERROR inserting/updating data in table TORP_WORKITEM: \n{e}", icon="🚨")
        conn.rollback()
        return False

    finally:
        if cursor:
            cursor.close() # Close the cursor in a finally block


def update_workitem(witem: dict, conn) -> bool:
    try:
        with conn:
            cursor = conn.cursor()        

        sql = """
        UPDATE TORP_WORKITEMS SET
            status = ?, 
            tskgrl1 = ?, 
            tskgrl2 = ?, 
            time_qty = ?, 
            description = ?, 
            note = ?
        WHERE woid = ?
        AND tdspid = ?
        AND refdate = ?
        """
        values = (
            witem["STATUS"], 
            witem["TSKGRL1"], 
            witem["TSKGRL2"],
            witem["TIME_QTY"], 
            witem["DESCRIPTION"], 
            witem["NOTE"],
            witem["WOID"], 
            witem["TDSPID"], 
            witem["REFDATE"]  
        )
        cursor.execute(sql, values)
        conn.commit()        
        return True
    except Exception as e:
        st.error(f"**ERROR updating data in table TORP_WORKITEM: \n{e}", icon="🚨")
        conn.rollback()
        return False

    finally:
        if cursor:
            cursor.close() # Close the cursor in a finally block


def delete_workitem(witem: dict, conn) ->  bool:
    """Delete workitem """
    try:
        cursor = conn.cursor()
        query = """
            DELETE FROM workitems
            WHERE REFDATE = ? 
            AND WOID = ? 
            AND TDSPID = ?
        """
        cursor.execute(query, (witem["REFDATE"], witem["WOID"], witem["TDSPID"]))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        st.error(f"**ERROR deleting data in table TORP_WORKITEM: \n{e}", icon="🚨")
        return False

    finally:
        if cursor:
            cursor.close() # Close the cursor in a finally block


def insert_wo_phase(row, conn):
    try:
        cursor = conn.cursor()
        insert_query = """
        INSERT INTO TORP_WO_PHASES (WOID, TDTLID, PHASE_CODE, STATUS, STARTDATE, ENDDATE, PROGRESS)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        conn.execute(insert_query, (
            row['WOID'],
            row['TDTLID'],
            row['PHASE_CODE'],
            row['STATUS'],
            row['STARTDATE'],
            row['ENDDATE'],
            row['PROGRESS']
        ))
    
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        st.error(f"**ERROR inserting data in table TORP_WO_PHASES: \n{e}", icon="🚨")
        return False

    finally:
        if cursor:
            cursor.close() # Close the cursor in a finally block

def update_wo_phase(row, conn):
    try:
        cursor = conn.cursor()
        update_query = """
        UPDATE TORP_WO_PHASES 
        SET STATUS = ?, STARTDATE = ?, ENDDATE = ?, PROGRESS = ?
        WHERE WOID = ? AND TDTLID = ? AND PHASE_CODE = ?
        """
        conn.execute(update_query, (
            row['STATUS'],
            row['STARTDATE'],
            row['ENDDATE'],
            row['PROGRESS'],
            row['WOID'],
            row['TDTLID'],
            row['PHASE_CODE']
        ))
    
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        st.error(f"**ERROR updating data in table TORP_WO_PHASES: \n{e}", icon="🚨")
        return False

    finally:
        if cursor:
            cursor.close() # Close the cursor in a finally block

#####################
def insert_wo_activity(row, conn):
    try:
        cursor = conn.cursor()
        insert_query = """
        INSERT INTO TORP_WORKACTIVITY (WOID, TDTLID, ACTGRP_L1, ACTGRP_L2, STATUS, STARTDATE, ENDDATE, PROGRESS, DESCRIPTION)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        conn.execute(insert_query, (
            row['WOID'],
            row['TDTLID'],
            row['ACTGRP_L1'],
            row['ACTGRP_L2'],
            row['STATUS'],
            row['STARTDATE'],
            row['ENDDATE'],
            row['PROGRESS'],
            row['DESCRIPTION']
        ))
    
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        st.error(f"**ERROR inserting data in table TORP_WORKACTIVITY: \n{e}", icon="🚨")
        return False

    finally:
        if cursor:
            cursor.close() # Close the cursor in a finally block

def update_wo_activity(row, conn):
    try:
        cursor = conn.cursor()
        # update_query = """
        # UPDATE TORP_WORKACTIVITY 
        # SET STATUS = ?, STARTDATE = ?, ENDDATE = ?, PROGRESS = ?, DESCRIPTION = ?
        # WHERE WOID = ? AND TDTLID = ? AND ACTGRP_L1 = ? AND ACTGRP_L2 = ?
        # """
        update_query = """
        # UPDATE TORP_WORKACTIVITY 
        # SET ACTGRP_L1 = ?, ACTGRP_L2 = ? , STATUS = ?, STARTDATE = ?, ENDDATE = ?, PROGRESS = ?, DESCRIPTION = ?
        # WHERE ROWID = ?       
        """
        conn.execute(update_query, (
            row['ACTGRP_L1'],
            row['ACTGRP_L2']               
            row['STATUS'],
            row['STARTDATE'],
            row['ENDDATE'],
            row['PROGRESS'],
            row['DESCRIPTION'],
            row['ROWID']        
        ))
    
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        st.error(f"**ERROR updating data in table TORP_WO_ACTIVITY: \n{e}", icon="🚨")
        return False

    finally:
        if cursor:
            cursor.close() # Close the cursor in a finally block
#####################


def initialize_session_state(conn): #passo la connessione
        # Load data only once and store in session state
    session_data = {
        'df_depts': load_dept_data,
        'df_users': load_users_data,
        'df_pline': load_pline_data,
        'df_pfamily': load_pfamily_data,
        'df_category': load_category_data,
        'df_type': load_type_data,
        'df_lk_type_category': load_lk_type_category_data,
        'df_lk_category_detail': load_lk_category_detail_data,
        'df_lk_pline_tdtl': load_lk_pline_tdtl_data,
        'df_permission': load_permission_data,
        'df_wo_phases': load_wo_phases_data,
        'df_wo_activity': load_wo_activity_data,  
        'df_detail': load_detail_data,
        'df_requests': load_requests_data,
        'df_reqassignedto': load_reqassignedto_data,
        'df_attachments': load_attachments_data,
        'df_workorders': load_workorders_data,
        'df_woassignedto': load_woassignedto_data,
        'df_workitems': load_workitems_data,
        'df_tskgrl1': load_tskgrl1_data,
        'df_tskgrl2': load_tskgrl2_data,
    }

    # for key, loader in session_data.items():
    #     if key not in st.session_state:
    #         st.session_state[key] = loader(conn)
    for key, loader in session_data.items():
        if key not in st.session_state or st.session_state[key] is None:  # Controllo più robusto
            try:
                st.session_state[key] = loader(conn)
            except Exception as e:  # Gestione errori
                st.error(f"Errore caricamento dati per {key}: {e}")
                st.stop()  # Importante: ferma l'esecuzione se il caricamento fallisce