import streamlit as st
import pandas as pd
import datetime
import time
from typing import Optional, Tuple, Dict, List
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode, ColumnsAutoSizeMode
from streamlit_option_menu import option_menu
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

def show_wo_phases_dialog(selected_row_dict, conn):
    
    #st.write(f"Number of workitems: `{len(df_to_display)}`")
    
    df_phases_wo = st.session_state.df_wo_phases[st.session_state.df_wo_phases["WOID"]==selected_row_dict["WOID"]]
    with st.container(border=True):
        edited_df = st.data_editor(
                        df_phases_wo, 
                        use_container_width=True, 
                        hide_index=False,
                        num_rows="dynamic"
                )

def show_workorder_dialog(selected_row_dict, conn):
    """Visualizza e gestisci la finestra di dialogo dell'ordine di lavoro."""
    wo_id = selected_row_dict["WOID"]
    wo_reqid = selected_row_dict["REQID"]
    wo_status_default = selected_row_dict["STATUS"]
    wo_title_default = selected_row_dict["TITLE"]
    popup_title = f"Request {wo_reqid}" 

    # Creazione di un contenitore per la sezione di modifica
    with st.container(border=True):
        #@st.dialog(popup_title, width="large")
        def dialog_content():
            st.markdown(
                """
                <style>
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

            wo_description_filtered = st.session_state.df_workorders[st.session_state.df_workorders["WOID"] == wo_id]["DESCRIPTION"]
            if not wo_description_filtered.empty:
                wo_description_default = wo_description_filtered.values[0]


            #woid = st.session_state.df_workorders[st.session_state.df_workorders["REQID"] == reqid]["WOID"]
            wo_type_options=["Standard", "APQP Project"]  #APQP -> ADVANCED PRODUCT QUALITY PLANNING"  
            wo_type_filtered = st.session_state.df_workorders[st.session_state.df_workorders["WOID"] == wo_id]["TYPE"]
            if not wo_type_filtered.empty:
                wo_type_default = wo_type_filtered.values[0]
                wo_type_index = wo_type_options.index(wo_type_default)
            else:
                wo_type_index = 0  

            wo_proj_class_options = ["", "OEM", "OTHER"]
            wo_proj_class_filtered = st.session_state.df_workorders[st.session_state.df_workorders["WOID"] == wo_id]["PROJ_CLASS"]
            if not wo_proj_class_filtered.empty:
                wo_proj_class_default = wo_proj_class_filtered.values[0]
                wo_proj_class_index = wo_proj_class_options.index(wo_proj_class_default)
            else:
                wo_proj_class_index = None  # O un valore di default appropriato

            # Gestione della data di inizio con None come default
            wo_startdate_filtered = st.session_state.df_workorders[st.session_state.df_workorders["WOID"] == wo_id]["STARTDATE"]

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


            wo_enddate_filtered = st.session_state.df_workorders[st.session_state.df_workorders["WOID"] == wo_id]["ENDDATE"]
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

            wo_timeqty_filtered = st.session_state.df_workorders[st.session_state.df_workorders["WOID"] == wo_id]["TIME_QTY"]
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

            wo_nr = st.text_input(
                        label=":orange[Work Order ID]", 
                        value=wo_id, 
                        disabled=True
            )

            wo_title = st.text_input(
                        label=":orange[Title](:red[*])", 
                        value=wo_title_default, 
                        disabled=False
            )

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
            (st.session_state.df_woassignedto['WOID'] == wo_id) & 
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
                    "woid": wo_id,
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
                    success = modules.sqlite_db.save_workorder_assignments(wo_id, wo_tdtl_code, wo_assignedto, st.session_state.df_users, st.session_state.df_woassignedto, conn)
                    # Update request status
                    #success = modules.sqlite_db.update_request(wo_reqid, "ASSIGNED", wo_req_note_td, "", [wo_tdtl_code], wo_req_duedate_td, conn)              
                    if success:
                        st.session_state.grid_refresh = True
                        st.session_state.grid_response = None
                        st.success(f"Work order {wo_id} updated successfully!")
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

    def create_grid(df):
        grid_builder = GridOptionsBuilder.from_dataframe(df)
        
        # Configurazione base delle colonne
        grid_builder.configure_default_column(
            resizable=True,
            filterable=True,
            sortable=True,
            editable=False,
            enableRowGroup=False
        )
        
        # Configurazione selezione riga
        grid_builder.configure_selection(
            selection_mode='single',
            use_checkbox=True,
            header_checkbox=True
        )
        
        # Altre configurazioni
        grid_builder.configure_pagination(paginationAutoPageSize=False, paginationPageSize=12)
        grid_builder.configure_grid_options(domLayout='normal')
        grid_builder.configure_column("WOID", cellStyle=cellStyle)
        
        grid_options = grid_builder.build()
        
        return AgGrid(
            df,
            gridOptions=grid_options,
            allow_unsafe_jscode=True,
            theme="balham",
            fit_columns_on_grid_load=False,
            update_mode=GridUpdateMode.SELECTION_CHANGED,  # Importante: reagisce ai cambi di selezione
            data_return_mode=DataReturnMode.AS_INPUT,
            key="main_grid"
        )


    modules.sqlite_db.initialize_session_state(conn)
    if "grid_data" not in st.session_state:
        st.session_state.grid_data = st.session_state.df_workorders.copy()
    if "grid_response" not in st.session_state:
        st.session_state.grid_response = None
    if "grid_refresh_key" not in st.session_state: 
        st.session_state.grid_refresh_key = "initial"    


    df_workorder_grid = pd.DataFrame()
    df_workorder_grid['WOID'] = st.session_state.df_workorders['WOID']
    df_workorder_grid['TDTL_NAME'] = st.session_state.df_workorders['TDTLID'].apply(lambda tdtl_code: modules.servant.get_description_from_code(st.session_state.df_users, tdtl_code, "NAME"))
    df_workorder_grid['STATUS'] = st.session_state.df_workorders['STATUS']
    df_workorder_grid['INSDATE'] = st.session_state.df_workorders['INSDATE']    
    df_workorder_grid['TYPE'] = st.session_state.df_workorders['TYPE']
    df_workorder_grid['REQID'] = st.session_state.df_workorders['REQID']
    df_workorder_grid['TITLE'] = st.session_state.df_workorders['TITLE']
        
    df_workorder_grid = pd.merge(
        df_workorder_grid,
        st.session_state.df_requests[['REQID', 'DUEDATE_TD']],
        on='REQID',
        how='left'
    )

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
    
    wo_tdtl_options = df_workorder_grid['TDTL_NAME'].drop_duplicates().sort_values()
    tdtl_filter = st.sidebar.selectbox(
        ":orange[TD Team Leader]", 
        wo_tdtl_options, 
        index=None,
        key='tdtl_value'
    )

    # Apply filters 
    filtered_data = df_workorder_grid.copy() 
    if status_filter: 
        filtered_data = filtered_data[filtered_data["STATUS"] == status_filter] 
    if tdtl_filter: 
        filtered_data = filtered_data[filtered_data["TDTL_NAME"] == tdtl_filter] 
    st.session_state.grid_data = filtered_data

    # Display grid and handle selection
    
    st.subheader(":orange[Work Order list]")
    st.session_state.grid_response = create_grid(st.session_state.grid_data)
    
    navbar_h_options = ["Home", "Refresh", "WO Header", "WO Phases"]
    navbar_h = option_menu(None, options=navbar_h_options, 
    icons=['house','play','book','activity'], 
    menu_icon="cast", default_index=0, orientation="horizontal"
    )
    #st.write(f"You have selecte option {navbar_h}")
    
    if navbar_h == "Refresh":
        reset_application_state()
        st.session_state.df_workorders = modules.sqlite_db.load_workorder_data(conn)  # Ricarica i dati dal database
    elif navbar_h == "WO Header" or navbar_h == "WO Phases":
        selected_rows_df = st.session_state.grid_response['selected_rows']
        
        if selected_rows_df is None or len(selected_rows_df) == 0:
            st.warning("Per favore seleziona una riga dalla griglia")
            return
        
        if navbar_h == "WO Header":
            st.subheader(":orange[Work Order detail]")
            selected_row_dict = selected_rows_df.iloc[0].to_dict()
            show_workorder_dialog(selected_row_dict, conn)
        elif navbar_h == "WO Phases":
            st.subheader(":orange[Work Order phase]")
            selected_row_dict = selected_rows_df.iloc[0].to_dict()
            show_wo_phases_dialog(selected_row_dict, conn)
    
    # # workorder_button_disable = not (selected_rows is not None and isinstance(selected_rows, pd.DataFrame) and not selected_rows.empty)
    # # workitem_button_disable = not (selected_rows is not None and isinstance(selected_rows, pd.DataFrame) and not selected_rows.empty)
    # workorder_button_disable = False
    # workitem_button_disable = False

    # # ... (Pulsanti e chiamate di dialogo)
    # #col1, col2, col3 = st.columns(3)
    # #with col1:
    
    # if st.button("🔄 Refresh data", type="secondary"):
    #     reset_application_state()
    #     st.session_state.df_workorders = modules.sqlite_db.load_workorder_data(conn)  # Ricarica i dati dal database
    
    # #with col2:
    # if st.button("✏️ Modify Work Order", type="secondary", disabled=workorder_button_disable):
    #     if st.session_state.grid_response and st.session_state.grid_response['selected_rows'] is not None and not st.session_state.grid_response['selected_rows'].empty:
    #         selected_rows_df = st.session_state.grid_response['selected_rows']
    #         selected_row_dict = selected_rows_df.iloc[0].to_dict() #oppure selected_rows_df.to_dict('records')[0]
    #         show_workorder_dialog(selected_row_dict, conn)

    # #with col3:
    # if st.button("🎯 Create Work Item", type="secondary", disabled=workitem_button_disable):
    #     if st.session_state.grid_response and st.session_state.grid_response['selected_rows'] is not None and not st.session_state.grid_response['selected_rows'].empty:
    #         selected_rows_df = st.session_state.grid_response['selected_rows']
    #         selected_row_dict = selected_rows_df.iloc[0].to_dict()  # oppure selected_rows_df.to_dict('records')[0]


def main():
    pass

if __name__ == "__main__":
    main()
else:
    manage_workorder(st.session_state.conn)            