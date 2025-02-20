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
STATUS_COMPLETED = "COMPLETED"
STATUS_ASSIGNED = "ASSIGNED"
REQ_STATUS_OPTIONS = ['NEW', 'PENDING', 'ASSIGNED', 'WIP', 'COMPLETED', 'DELETED']
WO_STATUS_OPTIONS = ['NEW', 'PENDING', 'ASSIGNED', 'WIP', 'COMPLETED', 'DELETED']


def show_workorder_dialog(selected_row_dict, conn):
    """Visualizza e gestisci la finestra di dialogo dell'ordine di lavoro."""
    woid = selected_row_dict["WOID"]
    wo_reqid = selected_row_dict["REQID"]
    wo_status_default = selected_row_dict["STATUS"]
    wo_title = selected_row_dict["TITLE"]
    popup_title = f"Request {wo_reqid}" 

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

        st.text_input(label="Request title", 
                value=wo_title, 
                disabled=True)       # Usa selected_row_dict
        wo_description_filtered = st.session_state.df_workorders[st.session_state.df_workorders["WOID"] == woid]["DESCRIPTION"]
        if not wo_description_filtered.empty:
            wo_description_default = wo_description_filtered.values[0]

        st.divider()
        st.subheader(f"Work Order {woid}")

        #woid = st.session_state.df_workorders[st.session_state.df_workorders["REQID"] == reqid]["WOID"]
        wo_type_options=["Standard", "APQP Project"]  #APQP -> ADVANCED PRODUCT QUALITY PLANNING"  
        wo_type_filtered = st.session_state.df_workorders[st.session_state.df_workorders["WOID"] == woid]["TYPE"]
        if not wo_type_filtered.empty:
            wo_type_default = wo_type_filtered.values[0]
            wo_type_index = wo_type_options.index(wo_type_default)
        else:
            wo_type_index = 0  

        wo_proj_class_options = ["", "OEM", "OTHER"]
        wo_proj_class_filtered = st.session_state.df_workorders[st.session_state.df_workorders["WOID"] == woid]["PROJ_CLASS"]
        if not wo_proj_class_filtered.empty:
            wo_proj_class_default = wo_proj_class_filtered.values[0]
            wo_proj_class_index = wo_proj_class_options.index(wo_proj_class_default)
        else:
            wo_proj_class_index = None  # O un valore di default appropriato

        # Gestione della data di inizio con None come default
        wo_startdate_filtered = st.session_state.df_workorders[st.session_state.df_workorders["WOID"] == woid]["STARTDATE"]

        if not wo_startdate_filtered.empty:
            start_date_value = wo_startdate_filtered.values[0]
            # Controllo specifico per "EMPTY STRING" o stringa vuota
            if start_date_value == "EMPTY STRING" or start_date_value == "":
                wo_startdate_default = None
            else:
                # Solo se abbiamo una data valida, proviamo a convertirla
                try:
                    start_date = pd.to_datetime(start_date_value)
                    wo_startdate_default = start_date.date()
                except:
                    wo_startdate_default = None
        else:
            wo_startdate_default = None


        wo_enddate_filtered = st.session_state.df_workorders[st.session_state.df_workorders["WOID"] == woid]["ENDDATE"]
        if not wo_enddate_filtered.empty:
            end_date_value = wo_enddate_filtered.values[0]
            # Controllo specifico per "EMPTY STRING" o stringa vuota
            if end_date_value == "EMPTY STRING" or end_date_value == "":
                wo_enddate_default = None
            else:
                # Solo se abbiamo una data valida, proviamo a convertirla
                try:
                    end_date = pd.to_datetime(end_date_value)
                    wo_enddate_default = end_date.date()
                except:
                    wo_enddate_default = None
        else:
            wo_enddate_default = None

        wo_timeqty_filtered = st.session_state.df_workorders[st.session_state.df_workorders["WOID"] == woid]["TIME_QTY"]
        if not wo_timeqty_filtered.empty:
            wo_timeqty_default = float(wo_timeqty_filtered.iloc[0])  # Converti a float!
            min_value = 0.0 # Valore minimo predefinito come float
        else:
            wo_timeqty_default = 0.0  # Valore di default come float
            min_value = 0.0 # Valore minimo predefinito come float             
                
        df_tdusers = st.session_state.df_users[st.session_state.df_users["DEPTCODE"] == "DTD"]
        
        # Lista dei possibili nomi dei Team Leader
        tdtl_usercode = st.session_state.df_lk_pline_tdtl["USER_CODE"].drop_duplicates().sort_values().tolist() #conversione in lista
        tdtl_username_list = st.session_state.df_users[st.session_state.df_users["CODE"].isin(tdtl_usercode)]["NAME"].tolist()

        tdtl_default_codes = st.session_state.df_reqassignedto[st.session_state.df_reqassignedto["REQID"] == wo_reqid]["TDTLID"].tolist()

        if tdtl_default_codes:
            tdtl_option = st.session_state.df_users[st.session_state.df_users["CODE"].isin(tdtl_default_codes)]
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

        
        wo_tdtl_name = st.selectbox(
            label=":orange[Tech Department Team Leader](:red[*])",
            options=tdtl_username_list,
            index=default_indices[0] if default_indices else None,  # Usa il primo indice se presente, altrimenti None
            key="sb_tdtl_reqmanage2",
            disabled=False
        )

        if wo_tdtl_name: #se è stato selezionato un TL
            wo_tdtl_code = st.session_state.df_users[st.session_state.df_users["NAME"] == wo_tdtl_name]["CODE"].iloc[0] #Recupero il codice del TL
        else:
            wo_tdtl_code = None # o un valore di default che preferisci            

        wo_type = st.selectbox(
            label=":orange[Type](:red[*])", 
            options=wo_type_options, 
            index=wo_type_index, 
            disabled=False)

        if wo_type == "APQP Project":
            wo_proj_class = st.selectbox(
                label=":orange[Project Class]", 
                options=wo_proj_class_options, 
                index=wo_proj_class_index, 
                disabled=False)
        else:
            wo_proj_class = ""        

        wo_status = st.selectbox(
            label=":orange[Status](:red[*])", 
            options=WO_STATUS_OPTIONS, 
            index=WO_STATUS_OPTIONS.index(wo_status_default), 
            disabled=False)


        wo_startdate = st.date_input(
            label=":orange[Start date](:red[*])", 
            #value=wo_startdate_default,
            value=wo_startdate_default,
            format="YYYY-MM-DD",
            key="startdate_input", 
            disabled=False
        )

        wo_enddate = st.date_input(
            label=":orange[End date](:red[*])", 
            #value=wo_enddate_default, 
            value=wo_enddate_default,
            format="YYYY-MM-DD",
            key="enddate_input", 
            disabled=False
        )

        wo_time_qty = st.number_input(
            label=":orange[Time estimated](:red[*]):",
            min_value=min_value, # Usa il valore minimo predefinito
            value=wo_timeqty_default if wo_timeqty_default is not None else 0, # Valore iniziale
            step=0.5)  
        
        wo_time_um = "H" 

        filtered_woassignedto = st.session_state.df_woassignedto[
          (st.session_state.df_woassignedto['WOID'] == woid) & 
          (st.session_state.df_woassignedto['TDTLID'] == wo_tdtl_code)
        ]  
               
        wo_assignedto_default_names = []  # Lista per i nomi predefiniti
        for code in filtered_woassignedto["TDSPID"]: # Itero sui codici
            name = modules.servant.get_description_from_code(df_tdusers, code, "NAME")
            wo_assignedto_default_names.append(name)

        wo_assignedto_option = list(df_tdusers["NAME"])
        wo_assignedto_label = ":orange[Tech Department Specialists assigned to] (:red[*]):"
        wo_assignedto = st.multiselect(
            label=wo_assignedto_label, 
            options=wo_assignedto_option, 
            default=wo_assignedto_default_names, 
            max_selections=3,
            disabled=False
        )
        
        wo_sequence = ""  # Valore di default per la sequenza
        wo_req_note_td = st.session_state.df_requests[st.session_state.df_requests["REQID"] == wo_reqid]["NOTE_TD"]
        
        if (wo_type == wo_type_default and 
            wo_assignedto == wo_assignedto_default_names and 
            wo_time_qty == wo_timeqty_default and 
            wo_status == wo_status_default and 
            wo_startdate == wo_startdate_default and
            wo_enddate == wo_enddate_default
            ):
            disable_save_button = True
        else:
            disable_save_button = False    

        if st.button("Save", type="primary", disabled=disable_save_button, key="wo_save_button"):
            wo = {
                "woid": woid,
                "tdtlid": wo_tdtl_code,
                "type": wo_type,
                "title": wo_title,  
                "description": wo_description_default,
                "time_qty": wo_time_qty,
                "time_um": wo_time_um,
                "status": STATUS_ASSIGNED,
                "startdate": wo_startdate,
                "enddate": wo_enddate,
                "reqid": wo_reqid,
                "insdate": wo_startdate_default,
                "sequence": wo_sequence,
                "proj_class": wo_proj_class,
            }
            # Save Workorder data
            wo_idrow, success = modules.sqlite_db.save_workorder(wo, conn)
            if success:
                #st.write(f"{woid} - {req_tdtl_code} - {wo_assignedto}- {st.session_state.df_user} - {st.session_state.df_woassignedto}")
                # Save Workorder assignments
                success = modules.sqlite_db.save_workorder_assignments(woid, wo_tdtl_code, wo_assignedto, st.session_state.df_users, st.session_state.df_woassignedto, conn)
                # Update request status
                #success = modules.sqlite_db.update_request(wo_reqid, "ASSIGNED", wo_req_note_td, "", [wo_tdtl_code], wo_req_duedate_td, conn)              
                if success:
                    st.session_state.grid_refresh = True
                    st.session_state.grid_response = None
                    st.success(f"Work order {woid} updated successfully!")
                    st.session_state.df_workorder = modules.sqlite_db.load_workorders_data(conn)  # Ricarica i dati dal database
                    st.session_state.need_refresh = True
                    time.sleep(3)
                    reset_application_state()
                    st.rerun()

    return dialog_content()


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

def manage_workorder(conn):

    # Initialize session state
    modules.sqlite_db.initialize_session_state(conn)
    if "grid_data" not in st.session_state:
        st.session_state.grid_data = st.session_state.df_workorders.copy()
    if "grid_response" not in st.session_state:
        st.session_state.grid_response = None
    if "grid_refresh_key" not in st.session_state: 
        st.session_state.grid_refresh_key = "initial"    


    df_workorder_grid = pd.DataFrame()
    df_workorder_grid['WOID'] = st.session_state.df_workorders['WOID']
    df_workorder_grid['TDTL_NAME'] = st.session_state.df_requests['TDTLID'].apply(lambda tdtl_code: modules.servant.get_description_from_code(st.session_state.df_users, tdtl_code, "NAME"))
    df_workorder_grid['STATUS'] = st.session_state.df_workorders['STATUS']
    df_workorder_grid['INSDATE'] = st.session_state.df_workorders['INSDATE']    
    df_workorder_grid['TYPE'] = st.session_state.df_workorders['TYPE']
    df_workorder_grid['REQID'] = st.session_state.df_workorders['REQID']
    df_workorder_grid['TITLE'] = st.session_state.df_workorders['TITLE']

    cellStyle = JsCode("""
        function(params) {
            if (params.column.colId === 'WOID') {
                       return {
                        'backgroundColor': '#8ebfde',
                        'color': '#000000',
                        'fontWeight': 'bold'
                    };
            }
            return null;
        }
        """)
    grid_builder = GridOptionsBuilder.from_dataframe(df_workorder_grid)
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
    grid_builder.configure_column("WOID", cellStyle=cellStyle)
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
        st.session_state.grid_data = df_workorder_grid.copy()  # Copia per evitare modifiche al DataFrame originale
    if "grid_response" not in st.session_state:
        st.session_state.grid_response = None


    # Sidebar controls - Filters
    st.sidebar.header(":blue[Filters]")
    wo_status_options = list(df_workorder_grid['STATUS'].drop_duplicates().sort_values())
    status_filter = st.sidebar.selectbox(
        ":orange[Status]", 
        wo_status_options, 
        index=None,
        key='Status_value'
    )
    
    wo_tdtl_options = df_workorder_grid['TDTLID'].drop_duplicates().sort_values()
    tdtl_filter = st.sidebar.selectbox(
        ":orange[TDTL Id]", 
        wo_tdtl_options, 
        index=None,
        key='tdtl_value'
    )

    # Apply filters 
    filtered_data = df_workorder_grid.copy() 
    if status_filter: 
        filtered_data = filtered_data[filtered_data["STATUS"] == status_filter] 
    if tdtl_filter: 
        filtered_data = filtered_data[filtered_data["TDTLID"] == tdtl_filter] 
    st.session_state.grid_data = filtered_data

    # Display grid
    st.subheader(":orange[Work Order list]")
    
    # Creazione/Aggiornamento della griglia (UNA SOLA VOLTA per ciclo di esecuzione)
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
    workorder_button_disable = not (selected_rows is not None and isinstance(selected_rows, pd.DataFrame) and not selected_rows.empty)
    workitem_button_disable = not (selected_rows is not None and isinstance(selected_rows, pd.DataFrame) and not selected_rows.empty)

    # ... (Pulsanti e chiamate di dialogo)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Refresh data", type="secondary"):
            reset_application_state()
            st.session_state.df_workorders = modules.sqlite_db.load_workorder_data(conn)  # Ricarica i dati dal database
    
    with col2:
        if st.button("✏️ Modify Work Order", type="secondary", disabled=workorder_button_disable):
            if st.session_state.grid_response and st.session_state.grid_response['selected_rows'] is not None and not st.session_state.grid_response['selected_rows'].empty:
                selected_rows_df = st.session_state.grid_response['selected_rows']
                selected_row_dict = selected_rows_df.iloc[0].to_dict() #oppure selected_rows_df.to_dict('records')[0]
                show_workorder_dialog(selected_row_dict, conn)

    with col3:
        if st.button("🎯 Create Work Item", type="secondary", disabled=workitem_button_disable):
            if st.session_state.grid_response and st.session_state.grid_response['selected_rows'] is not None and not st.session_state.grid_response['selected_rows'].empty:
                selected_rows_df = st.session_state.grid_response['selected_rows']
                selected_row_dict = selected_rows_df.iloc[0].to_dict()  # oppure selected_rows_df.to_dict('records')[0]
                #show_workitem_dialog(selected_row_dict, conn)
            # else:
            #     st.warning("Please select a request from the grid first.", icon="⚠️")  # Avvisa l'utent# ... (Resto del tuo codice)

def main():
    pass

if __name__ == "__main__":
    main()
else:
    manage_workorder(st.session_state.conn)            