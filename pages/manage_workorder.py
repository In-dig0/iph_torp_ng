# 3th party packages
import streamlit as st
import pandas as pd
#from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode, ColumnsAutoSizeMode
from streamlit_option_menu import option_menu
# Built-in packages
import datetime
import time
from typing import Optional, Tuple, Dict, List
# App modules
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
    # Ottieni il DataFrame filtrato
    #df_phases_wo = st.session_state.df_wo_phases[st.session_state.df_wo_phases["WOID"]==selected_row_dict["WOID"]]
    df_wo_activity = st.session_state.df_wo_activity[st.session_state.df_wo_activity["WOID"]==selected_row_dict["WOID"]]
    # Resetta l'indice e rimuovi la colonna dell'indice se presente
    #df_phases_wo = df_phases_wo.reset_index(drop=True)
    df_wo_activity = df_wo_activity.reset_index(drop=True)

    # Converti le colonne delle date da stringa a datetime
    # df_phases_wo['STARTDATE'] = pd.to_datetime(df_phases_wo['STARTDATE'])
    # df_phases_wo['ENDDATE'] = pd.to_datetime(df_phases_wo['ENDDATE'])

    df_wo_activity['STARTDATE'] = pd.to_datetime(df_wo_activity['STARTDATE'])
    df_wo_activity['ENDDATE'] = pd.to_datetime(df_wo_activity['ENDDATE'])

    # Task Group Level 1 dropdown
    tskgrl1_options = st.session_state.df_tskgrl1["NAME"].tolist()
    tskgrl1_options = sorted(tskgrl1_options)
    tskgrl2_options = st.session_state.df_tskgrl2["NAME"].tolist()
    tskgrl2_options = sorted(tskgrl2_options)
    #selected_tskgrl1_code = modules.servant.get_code_from_name(st.session_state.df_tskgrl1, selected_tskgrl1, "CODE")
    selected_tdtlid = modules.servant.get_code_from_name(st.session_state.df_users, selected_row_dict["TDTL_NAME"], "CODE")
    # Task Group Level 2 dropdown (dependent on Level 1)
    # tskgrl2_options = st.session_state.df_tskgrl2[st.session_state.df_tskgrl2['PCODE'] == selected_tskgrl1_code]['NAME'].unique()
    # selected_tskgrl2 = st.selectbox(label=":blue[TaskGroup L2]", options=tskgrl2_options, index=None, key="sb_tskgrl2")
    # selected_tskgrl2_code = modules.servant.get_code_from_name(st.session_state.df_tskgrl2, selected_tskgrl2, "CODE")

    with st.container(border=True):
        # Editor dei dati con configurazione aggiuntiva
        edited_df = st.data_editor(
            df_wo_activity,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            column_config={
                "WOID": st.column_config.TextColumn(
                    "WOID",
                    help="Work Order ID",
                    default=selected_row_dict["WOID"]
                ),
                "TDTLID": st.column_config.TextColumn(
                    "TDTLID",
                    help="Team Leader ID",
                    default=selected_tdtlid
                ),
                "ACTGRP_L1": st.column_config.SelectboxColumn(
                    label="ACTIVITY_GRP_L1",
                    help="Activity Group L1",
                    options=tskgrl1_options
                ),
                "ACTGRP_L2": st.column_config.SelectboxColumn(
                    label="ACTIVITY_GRP_L2",
                    help="Activity Group L2",
                    options=tskgrl2_options
                ),                
                "STATUS": st.column_config.SelectboxColumn(
                    "STATUS",
                    help="Status",
                    options=[
                        "TO_START",
                        "IN_PROGRESS",
                        "COMPLETED",
                        "CANCELLED"
                    ]
                ),
                "STARTDATE": st.column_config.DateColumn(
                    "STARTDATE",
                    help="Start Date",
                    # min_value=datetime(2025, 1, 1),
                    # max_value=datetime(2025, 12, 31),
                    format="YYYY-MM-DD"
                ),
                "ENDDATE": st.column_config.DateColumn(
                    "ENDDATE",
                    help="End Date",
                    # min_value=datetime(2025, 1, 1),
                    # max_value=datetime(2025, 12, 31),
                    format="YYYY-MM-DD"
                ),
                "PROGRESS": st.column_config.NumberColumn(
                    "PROGRESS",
                    help="Progress (%)",
                    min_value=0,
                    max_value=100,
                    step=5,
                    default=0
                )
            }
        )
        
        if st.button("Save"):
            try:
                # Converti le date in formato stringa per il database
                edited_df['STARTDATE'] = edited_df['STARTDATE'].dt.strftime('%Y-%m-%d')
                edited_df['ENDDATE'] = edited_df['ENDDATE'].dt.strftime('%Y-%m-%d')
                
                # Verifica se ci sono più righe nell'edited_df rispetto all'originale
                if len(edited_df) > len(df_wo_activity):
                    # Ottieni le nuove righe
                    new_rows = edited_df.iloc[len(df_wo_activity):]
                    
                    for _, row in new_rows.iterrows():
                        #st.info(f"{row["ACTGRP_L1"]}-{row["ACTGRP_L2"]}")
                        actgrp_l1_code = modules.servant.get_code_from_name(st.session_state.df_tskgrl1, row["ACTGRP_L1"], "CODE")
                        actgrp_l2_code = modules.servant.get_code_from_name(st.session_state.df_tskgrl2, row["ACTGRP_L2"], "CODE")
                        wa = {
                            "WOID": row["WOID"], 
                            "TDTLID": row["TDTLID"], 
                            "ACTGRP_L1": actgrp_l1_code, 
                            "ACTGRP_L2": actgrp_l2_code, 
                            "STATUS": row["STATUS"],
                            "STARTDATE": row["STARTDATE"],
                            "ENDDATE": row["ENDDATE"],
                            "PROGRESS": row["PROGRESS"],
                            "DESCRIPTION": row["DESCRIPTION"]
                            }
                        st.info(wa) 
                        time.sleep(5)   
                        rc = modules.sqlite_db.insert_wo_activity(wa, conn)
                        time.sleep(5)   
                    
                    st.success("New work activity added successfully!")
                    st.session_state.df_wo_activity = modules.sqlite_db.load_wo_activity_data(conn)
                
                elif not edited_df.equals(df_wo_activity):
                    for index, row in edited_df.iterrows():
                        rc = modules.sqlite_db.update_wo_update_wo_activity(row, conn)                   
                    conn.commit()
                    st.success("Update successfully!")                    
                    st.session_state.df_wo_activity = modules.sqlite_db.load_wo_activity_data(conn)

                else:
                    st.info("Nothing to save!")
                    
            except Exception as e:
                st.error(f"Error saving data in TORP_WO_ACTIVITY: {str(e)}")
                st.write("Row data:", row.to_dict())
                
    return edited_df


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

    # Navbar
    navbar_h_options = ["Home", "Refresh", "Modify Work Order", "WO Activity"]
    
    navbar_h = option_menu(None, options=navbar_h_options, 
        icons=['house','arrow-counterclockwise','book','clipboard-pulse'], 
        menu_icon="cast", default_index=0, orientation="horizontal",
        styles={
        "container": {"padding": "0!important", "background-color": "#fafafa"},
        "icon": {"color": "orange", "font-size": "15px"}, 
        "nav-link": {"font-size": "15px", "text-align": "left", "margin":"0px"},
        "nav-link-selected": {"background-color": "grey"},
        }
    )

    # Create grid
    st.subheader(":orange[Work Order list]")
    st.session_state.grid_response = modules.servant.create_grid(st.session_state.grid_data, "main_grid")
   
   
    if navbar_h == "Refresh":
        reset_application_state()
        st.session_state.df_workorders = modules.sqlite_db.load_workorder_data(conn)  # Ricarica i dati dal database
    elif navbar_h == "Modify Work Order" or navbar_h == "WO Activity":
        selected_rows_df = st.session_state.grid_response['selected_rows']
        
        if selected_rows_df is None or len(selected_rows_df) == 0:
            st.warning("Please select a grid row first!", icon="⚠️")
            return
        
        if navbar_h == "Modify Work Order":
            st.subheader(":orange[Work Order detail]")
            selected_row_dict = selected_rows_df.iloc[0].to_dict()
            show_workorder_dialog(selected_row_dict, conn)
        elif navbar_h == "WO Activity":
            st.subheader(":orange[WO Activity]")
            selected_row_dict = selected_rows_df.iloc[0].to_dict()
            show_wo_phases_dialog(selected_row_dict, conn)
    

def main():
    pass

if __name__ == "__main__":
    main()
else:
    manage_workorder(st.session_state.conn)            