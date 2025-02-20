import streamlit as st
import pandas as pd
import datetime
import time
from typing import Optional, Tuple, Dict, List
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode, ColumnsAutoSizeMode
# Internal app module
import modules.servant
import modules.sqlite_db

# Global constants
ACTIVE_STATUS = "ACTIVE"
DISABLED_STATUS = "DISABLED"
DEFAULT_DEPT_CODE = "DTD"
STATUS_NEW = "NEW"
STATUS_WIP = "WIP"
REQ_STATUS_OPTIONS = ['NEW', 'PENDING', 'ASSIGNED', 'WIP', 'COMPLETED', 'DELETED']
SEQUENCE_NORMAL = ""

# ... (Caricamento dei dati nello stato della sessione come prima)

def reset_application_state():
    """Reset all session state variables and cached data"""
    # Lista delle chiavi di sessione da eliminare
    keys_to_clear = [
        'grid_data',
        'grid_response',
        'dialog_shown',
        'need_refresh',
        'main_grid',  # Chiave della griglia AgGrid
#            'Status_value',  # Chiave del filtro status nella sidebar
        'selected_rows' # Chiave della selezione delle righe
    ]
    
    # Rimuovi tutte le chiavi di sessione specificate
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    # Forza il refresh cambiando la chiave 
    st.session_state.grid_refresh_key = str(time.time())     
    st.rerun()

def show_request_dialog(selected_row_dict, req_status_options, update_request_fn, conn):  # Passa un dizionario
    """Visualizza e gestisci la finestra di dialogo di modifica della richiesta."""

    popup_title = f'Richiesta {selected_row_dict["REQID"]}'  # Accedi a REQID direttamente

    @st.dialog(popup_title, width="large")
    def dialog_content():

        reqid = selected_row_dict["REQID"] # Usa direttamente il dizionario

        description = st.session_state.df_requests.loc[st.session_state.df_requests["REQID"] == reqid, "DESCRIPTION"].values[0]
        st.text_area(
            label="Description", 
            value=description, 
            disabled=True)

        req_priority_options = ["High", "Medium", "Low"]
        idx_priority = req_priority_options.index(selected_row_dict['PRIORITY'])
        req_priortiy = st.selectbox(
            label=":orange[Priority](:red[*])", 
            options=req_priority_options, 
            index=idx_priority, 
            disabled=False, 
            key="priority_selectbox"
        )

        req_duedate = st.date_input(
            label=":orange[Desired due date](:red[*])", 
            value=selected_row_dict['DUEDATE'], 
            format="YYYY-MM-DD",
            key="duedate_input", 
            disabled=False
        )

        idx_status = req_status_options.index(selected_row_dict['STATUS'])  # Usa selected_row_dict
        req_status = st.selectbox(
            label=":orange[Status](:red[*])", 
            options=req_status_options, 
            index=idx_status, 
            key="status_selectbox",
            disabled=False
        )

        st.divider()
        tdtl_usercode = st.session_state.df_lk_pline_tdtl["USER_CODE"].drop_duplicates().sort_values().tolist() #conversione in lista
        tdtl_username_list = st.session_state.df_users[st.session_state.df_users["CODE"].isin(tdtl_usercode)]["NAME"].tolist()

        tdtl_default_codes = st.session_state.df_reqassignedto[st.session_state.df_reqassignedto["REQID"] == reqid]["TDTLID"].tolist()

        if tdtl_default_codes:
            tdtl_option = st.session_state.df_users[st.session_state.df_users["CODE"].isin(tdtl_default_codes)]
            default_tdtl_name = tdtl_option["NAME"].tolist()
        else:
            default_tdtl_name = []

        req_tdtl_name = st.multiselect(
            label=":orange[Tech Department Team Leader](:red[*])",
            options=tdtl_username_list,
            default=default_tdtl_name,
            key="sb_tdtl_reqmanage",
            disabled=False
        )

        if req_tdtl_name:
            req_tdtl_code = st.session_state.df_users[st.session_state.df_users["NAME"].isin(req_tdtl_name)]["CODE"].tolist()
        else:
            req_tdtl_code = []


        # Display Tech Dept Note
        default_note_td = str(st.session_state.df_requests[st.session_state.df_requests["REQID"] == reqid]["NOTE_TD"].values[0])
        req_note_td = st.text_area(
            label=":orange[Tech Department Notes]", 
            value=default_note_td, 
            disabled=False
        )

        # Display Tech Dept Note
        default_duedate_td = st.session_state.df_requests[st.session_state.df_requests["REQID"] == reqid]["DUEDATE_TD"].values[0]
        req_duedate_td = st.date_input(
            label=":orange[TD condirmed due date]", 
            value=default_duedate_td, 
            format="YYYY-MM-DD",            
            disabled=False
        )        

        if (req_note_td == default_note_td) and (selected_row_dict['STATUS'] == req_status) and (req_tdtl_name == default_tdtl_name) and (req_duedate_td == default_duedate_td): #Usa selected_row_dict
            disable_save_button = True
        else:
            disable_save_button = False   

        if st.button("Salva", type="primary", disabled=disable_save_button, key="req_save_button"):
            success = update_request_fn(reqid, req_status, req_note_td, 0, req_tdtl_code, req_duedate_td, conn)
            if success:
              st.session_state.grid_refresh = True
              st.session_state.grid_response = None
              st.success(f"Request {reqid} updated successfully!")
              st.session_state.df_requests = modules.sqlite_db.load_requests_data(conn)  # Ricarica i dati dal database
              st.session_state.need_refresh = True
              time.sleep(3)
              reset_application_state()
              st.rerun()


    return dialog_content()

def show_workorder_dialog(selected_row_dict,  # Passa un dizionario
                         df_workorders, df_woassignedto, df_users, new_status, 
                         default_dept_code, req_status_options, save_workorder_fn, 
                         save_woassignments_fn, conn):
    """Visualizza e gestisci la finestra di dialogo dell'ordine di lavoro."""

    popup_title = f'Richiesta {selected_row_dict["REQID"]}' # Accedi a REQID direttamente

    @st.dialog(popup_title, width="large")
    def dialog_content():
        st.markdown(
            """
            <style>
            div[data-testid="stTextInput"] > div > div > input:not([disabled]) {
                color: #28a745;
                border: 2px solid #28a745;
                -webkit-text-fill-color: #28a745 !important;
                font-weight: bold;
            }

            div[data-testid="stTextInput"] > div > div input[disabled] {
                color: #6c757d !important;
                opacity: 1 !important;
                -webkit-text-fill-color: #6c757d !important;
                background-color: #e9ecef !important;
                border: 1px solid #ced4da !important;
                font-style: italic;
            }

            .stSelectbox > div > div > div > div {
                color: #007bff;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # Caricamento lazy e controllo esplicito *QUI*
        if "df_user" not in st.session_state or st.session_state.df_user is None:
            try:
                st.session_state.df_user = modules.sqlite_db.load_users_data(conn)  # Carica *solo* se necessario
            except Exception as e:
                st.error(f"Errore caricamento dati df_user: {e}")
                st.stop()

        # Caricamento lazy e controllo esplicito *QUI*
        if "df_woassignedto" not in st.session_state or st.session_state.df_woassignedto is None:
            try:
                st.session_state.df_woassignedto = modules.sqlite_db.load_woassignedto_data(conn)
            except Exception as e:
                st.error(f"Errore caricamento dati df_woassignedto: {e}")
                st.stop()

        reqid = selected_row_dict["REQID"]  # Usa direttamente il dizionario
        woid = "W" + selected_row_dict["REQID"][1:]
        

        # ... (Resto del contenuto del dialogo, usando selected_row_dict)
        # Display request details
        st.text_input(label="Product Line", value=selected_row_dict['PRLINE_NAME'], disabled=True)  # Usa selected_row_dict
        st.text_input(label="Request title", value=selected_row_dict['TITLE'], disabled=True)       # Usa selected_row_dict
        req_description = st.session_state.df_requests.loc[st.session_state.df_requests["REQID"] == reqid, "DESCRIPTION"]
        if not req_description.empty:
            req_description_default = req_description.values[0]
        else:
            req_description_default = ""
        st.text_input(label="Descrizione della richiesta", value=req_description_default, disabled=True)

        req_note_td = st.session_state.df_requests[st.session_state.df_requests["REQID"]==reqid]["NOTE_TD"]
        if not req_note_td.empty:
            req_note_td_default = req_note_td.values[0]
        else:
            req_note_td_default = ""

        st.divider()
        st.subheader(f"Work Order {woid}")

        wo_nr = st.session_state.df_workorders[st.session_state.df_workorders["REQID"] == reqid]["WOID"]

        wo_type_options=["Standard", "APQP Project"]  #APQP -> ADVANCED PRODUCT QUALITY PLANNING"  
        wo_type_filtered = st.session_state.df_workorders[st.session_state.df_workorders["WOID"] == woid]["TYPE"]
        if not wo_type_filtered.empty:
            wo_type_default = wo_type_filtered.values[0]
            wo_type_index = wo_type_options.index(wo_type_default)
        else:
            wo_type_index = 0  

        wo_insdate_filtered = st.session_state.df_workorders[st.session_state.df_workorders["WOID"] == woid]["INSDATE"]
        if not wo_insdate_filtered.empty:
            wo_insdate_default = wo_insdate_filtered.values[0]
        else:
            wo_insdate_default = datetime.datetime.now().strftime("%Y-%m-%d")  # O un valore di default appropriato


        wo_startdate_filtered = st.session_state.df_workorders[st.session_state.df_workorders["WOID"] == woid]["STARTDATE"]
        if not wo_startdate_filtered.empty:
            wo_startdate_default = wo_startdate_filtered.values[0]
        else:
            wo_startdate_default = None  # O un valore di default appropriato

        wo_enddate_filtered = st.session_state.df_workorders[st.session_state.df_workorders["WOID"] == woid]["ENDDATE"]
        if not wo_enddate_filtered.empty:
            wo_enddate_default = wo_enddate_filtered.values[0]
        else:
            wo_enddate_default = None  # O un valore di default appropriato

        wo_timeqty_filtered = st.session_state.df_workorders[st.session_state.df_workorders["WOID"] == woid]["TIME_QTY"]
        if not wo_timeqty_filtered.empty:
            wo_timeqty_default = float(wo_timeqty_filtered.iloc[0])  # Converti a float!
            min_value = 0.0 # Valore minimo predefinito come float
        else:
            wo_timeqty_default = 0.0  # Valore di default come float
            min_value = 0.0 # Valore minimo predefinito come float             
                
        df_tdusers = df_users[df_users["DEPTCODE"] == default_dept_code]
        
        # Lista dei possibili nomi dei Team Leader
        tdtl_usercode = st.session_state.df_lk_pline_tdtl["USER_CODE"].drop_duplicates().sort_values().tolist() #conversione in lista
        tdtl_username_list = st.session_state.df_users[st.session_state.df_users["CODE"].isin(tdtl_usercode)]["NAME"].tolist()

        tdtl_default_codes = st.session_state.df_reqassignedto[st.session_state.df_reqassignedto["REQID"] == reqid]["TDTLID"].tolist()

        if tdtl_default_codes:
            tdtl_option = df_users[df_users["CODE"].isin(tdtl_default_codes)]
            default_tdtl_name = tdtl_option["NAME"].tolist()
        else:
            default_tdtl_name = []

        if default_tdtl_name:
            # Trova gli indici dei Team Leader predefiniti nella lista di opzioni
            default_indices = []
            for name in default_tdtl_name:
                try:
                    index = tdtl_username_list.index(name)
                    default_indices.append(index)
                except ValueError:
                    # Gestisci il caso in cui il nome predefinito non è presente nelle opzioni
                    st.warning(f"Il Team Leader '{name}' non trovato nella lista di opzioni.", icon="⚠️")
        else:
            default_indices = []

        req_tdtl_name = st.selectbox(
            label=":orange[Tech Department Team Leader](:red[*])",
            options=tdtl_username_list,
            index=default_indices[0] if default_indices else None,  # Usa il primo indice se presente, altrimenti None
            key="sb_tdtl_reqmanage2",
            disabled=False
        )

        if req_tdtl_name: #se è stato selezionato un TL
            req_tdtl_code = df_users[df_users["NAME"] == req_tdtl_name]["CODE"].iloc[0] #Recupero il codice del TL
        else:
            req_tdtl_code = None # o un valore di default che preferisci            

        wo_type = st.selectbox(label=":orange[Type](:red[*])", options=wo_type_options, index=wo_type_index, disabled=False)
        wo_time_qty = st.number_input(
            label=":orange[Time estimated](:red[*])",
            min_value=min_value, # Usa il valore minimo predefinito
            value=wo_timeqty_default if wo_timeqty_default is not None else 0, # Valore iniziale
            step=0.5
        )  
        wo_time_um = "H" 

        filtered_woassignedto = df_woassignedto[
          (df_woassignedto['WOID'] == woid) & 
          (df_woassignedto['TDTLID'] == req_tdtl_code)
        ]  # Usa isin()
               
        wo_assignedto_default_names = []  # Lista per i nomi predefiniti
        for code in filtered_woassignedto["TDSPID"]: # Itero sui codici
            name = modules.servant.get_description_from_code(df_tdusers, code, "NAME")
            wo_assignedto_default_names.append(name)

        wo_assignedto_option = list(df_tdusers["NAME"])
        wo_assignedto_title = ":orange[Tech Department Specialists assigned to](:red[*])"
        wo_assignedto = st.multiselect(
            label=wo_assignedto_title, 
            options=wo_assignedto_option, 
            default=wo_assignedto_default_names, 
            max_selections=3,
            disabled=False
        )
        
        wo_startdate = None
        wo_enddate = None     

        if not wo_nr.empty:
            if (wo_type == wo_type_default and wo_assignedto == wo_assignedto_default_names and wo_time_qty == wo_timeqty_default):
                disable_save_button = True
            else:
                disable_save_button = False    
        else:
            if not (wo_type and wo_assignedto and wo_time_qty):
                disable_save_button = True
            else:
                disable_save_button = False


        if st.button("Salva", type="primary", disabled=disable_save_button, key="wo_save_button"):
            insdate = datetime.datetime.now().strftime("%Y-%m-%d")
            wo = {
                "woid": woid,
                "tdtlid": req_tdtl_code,
                "type": wo_type,
                "title": selected_row_dict['TITLE'],  # Usa selected_row_dict
                "description": req_description_default,
                "time_qty": wo_time_qty,
                "time_um": wo_time_um,
                "status": STATUS_NEW,
                "startdate": wo_startdate,
                "enddate": wo_enddate,
                "reqid": reqid,
                "insdate": wo_insdate_default,
                "sequence": SEQUENCE_NORMAL
            }
            wo_idrow, success = modules.sqlite_db.save_workorder(wo, conn)
            if success:
                #st.write(f"{woid} - {req_tdtl_code} - {wo_assignedto}- {st.session_state.df_user} - {st.session_state.df_woassignedto}")
                success = modules.sqlite_db.save_workorder_assignments(woid, req_tdtl_code, wo_assignedto, st.session_state.df_users, st.session_state.df_woassignedto, conn)
                success = modules.sqlite_db.update_request(reqid, "ASSIGNED", req_note_td, "", [req_tdtl_code], conn)
                if success:
                    st.session_state.grid_refresh = True
                    st.session_state.grid_response = None
                    st.success(f"Work order {woid} created successfully!")
                    st.session_state.df_requests = modules.sqlite_db.load_requests_data(conn)  # Ricarica i dati dal database
                    st.session_state.df_workorders = modules.sqlite_db.load_workorders_data(conn)
                    st.session_state.df_woassignedto = modules.sqlite_db.load_woassignedto_data(conn) 
                    st.session_state.need_refresh = True
                    time.sleep(3)
                    reset_application_state()
                    st.rerun()

    return dialog_content()


def manage_request(conn):
    modules.sqlite_db.initialize_session_state(conn)
    # Initialize session state
    if "grid_data" not in st.session_state:
        st.session_state.grid_data = st.session_state.df_requests.copy()
    if "grid_response" not in st.session_state:
        st.session_state.grid_response = None
    if "grid_refresh_key" not in st.session_state: 
        st.session_state.grid_refresh_key = "initial"    


    df_requests_grid = pd.DataFrame()
    df_requests_grid['REQID'] = st.session_state.df_requests['REQID']
    df_requests_grid['STATUS'] = st.session_state.df_requests['STATUS']
    df_requests_grid['INSDATE'] = st.session_state.df_requests['INSDATE']
    df_requests_grid['DUEDATE'] = st.session_state.df_requests['DUEDATE']
    df_requests_grid['PRIORITY'] = st.session_state.df_requests['PRIORITY']
    df_requests_grid['PRLINE_NAME'] = st.session_state.df_requests['PR_LINE'].apply(lambda pline_code: modules.servant.get_description_from_code(st.session_state.df_pline, pline_code, "NAME"))
    df_requests_grid['TITLE'] = st.session_state.df_requests['TITLE']
    df_requests_grid['REQUESTER_NAME'] = st.session_state.df_requests['REQUESTER'].apply(lambda requester_code: modules.servant.get_description_from_code(st.session_state.df_users, requester_code, "NAME"))

    cellStyle = JsCode("""
        function(params) {
            if (params.column.colId === 'REQID') {
                       return {
                        'backgroundColor': '#8ebfde',
                        'color': '#000000',
                        'fontWeight': 'bold'
                    };
            }
            return null;
        }
        """)
    grid_builder = GridOptionsBuilder.from_dataframe(df_requests_grid)
    # makes columns resizable, sortable and filterable by default
    grid_builder.configure_default_column(
        resizable=True,
        filterable=True,
        sortable=True,
        editable=False,
        enableRowGroup=False
    )
    # Enalble pagination
    grid_builder.configure_pagination(paginationAutoPageSize=False, paginationPageSize=12)
    grid_builder.configure_grid_options(domLayout='normal')
    grid_builder.configure_column("REQID", cellStyle=cellStyle)
    grid_builder.configure_selection(
    selection_mode='single',     # Enable multiple row selection
    use_checkbox=True,             # Show checkboxes for selection
    header_checkbox=True
    )
    grid_options = grid_builder.build()
    # List of available themes
    available_themes = ["streamlit", "alpine", "balham", "material"]
    
    # Inizializzazione della sessione
    if "grid_data" not in st.session_state:
        st.session_state.grid_data = df_requests_grid.copy()  # Copia per evitare modifiche al DataFrame originale
    if "grid_response" not in st.session_state:
        st.session_state.grid_response = None


    # Sidebar controls - Filters
    st.sidebar.header(":blue[Filters]")
    req_status_options = list(df_requests_grid['STATUS'].drop_duplicates().sort_values())
    status_filter = st.sidebar.selectbox(
        ":orange[Status]", 
        req_status_options, 
        index=None,
        key='Status_value'
    )
    
    req_pline_options = df_requests_grid['PRLINE_NAME'].drop_duplicates().sort_values()
    pline_filter = st.sidebar.selectbox(
        ":orange[Product Line]", 
        req_pline_options, 
        index=None,
        key='Pline_value'
    )

    # Apply filters 
    filtered_data = df_requests_grid.copy() 
    if status_filter: 
        filtered_data = filtered_data[filtered_data["STATUS"] == status_filter] 
    if pline_filter: 
        filtered_data = filtered_data[filtered_data["PRLINE_NAME"] == pline_filter] 
    st.session_state.grid_data = filtered_data

    # Display grid
    st.subheader(":orange[Request list]")
    

    st.session_state.grid_response = AgGrid(
        st.session_state.grid_data,
        gridOptions=grid_options,
        allow_unsafe_jscode=True,
        theme=available_themes[2],
        fit_columns_on_grid_load=False,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        data_return_mode=DataReturnMode.AS_INPUT,
        key="main_grid"
    )


    selected_rows = st.session_state.grid_response['selected_rows']
    modify_request_button_disable = not (selected_rows is not None and isinstance(selected_rows, pd.DataFrame) and not selected_rows.empty)
    workorder_button_disable = not (selected_rows is not None and isinstance(selected_rows, pd.DataFrame) and not selected_rows.empty)

    # ... (Pulsanti e chiamate di dialogo)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Refresh data", type="secondary"):
            reset_application_state()
            st.session_state.df_requests = modules.sqlite_db.load_requests_data(conn)  # Ricarica i dati dal database
            st.session_state.df_workorders = modules.sqlite_db.load_workorders_data(conn)
            st.session_state.df_woassignedto = modules.sqlite_db.load_woassignedto_data(conn)
    with col2:
        if st.button("✏️ Modify Request", type="secondary", disabled=modify_request_button_disable):
            if st.session_state.grid_response and st.session_state.grid_response['selected_rows'] is not None and not st.session_state.grid_response['selected_rows'].empty:
                selected_rows_df = st.session_state.grid_response['selected_rows']
                selected_row_dict = selected_rows_df.iloc[0].to_dict() #oppure selected_rows_df.to_dict('records')[0]
                show_request_dialog(selected_row_dict, REQ_STATUS_OPTIONS, modules.sqlite_db.update_request, conn)
            # else:
            #     st.warning("Please select a request from the grid first.", icon="⚠️")
    with col3:
        if st.button("📌 Create Work Oder", type="secondary", disabled=workorder_button_disable):
            if st.session_state.grid_response and st.session_state.grid_response['selected_rows'] is not None and not st.session_state.grid_response['selected_rows'].empty:
                selected_rows_df = st.session_state.grid_response['selected_rows']
                selected_row_dict = selected_rows_df.iloc[0].to_dict()  # oppure selected_rows_df.to_dict('records')[0]
                show_workorder_dialog(selected_row_dict, st.session_state.df_workorders, st.session_state.df_woassignedto, st.session_state.df_users, STATUS_NEW, DEFAULT_DEPT_CODE, REQ_STATUS_OPTIONS, modules.sqlite_db.save_workorder, modules.sqlite_db.save_workorder_assignments, conn)
            # else:
            #     st.warning("Please select a request from the grid first.", icon="⚠️")  # Avvisa l'utent# ... (Resto del tuo codice)


def main():
    pass

if __name__ == "__main__":
    main()
else:
    manage_request(st.session_state.conn) 