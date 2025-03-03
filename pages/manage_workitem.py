# 3th party packages
import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
import calendar as std_cal
# Built-in packages
import time
from typing import Optional, Tuple, Dict, List
from datetime import datetime, timedelta, date
# Internal app module
import modules.sqlite_db
import modules.servant


def create_workitem(conn)-> None:

    def show_calendar():
        # Inizializza il flag se non esiste
        if 'calendar_needs_update' not in st.session_state:
            st.session_state.calendar_needs_update = False

        now = datetime.now()
        ultimo_giorno = std_cal.monthrange(now.year, now.month)[1]
        last_day_current_month = datetime(now.year, now.month, ultimo_giorno)
        first_day_current_month = datetime(now.year, now.month, 1)
        last_day_previous_month = first_day_current_month - timedelta(days=1)
        first_day_previous_month = datetime(last_day_previous_month.year, last_day_previous_month.month, 1)

        # Inizializza il dizionario degli eventi se non esiste
        if 'event_details' not in st.session_state:
            st.session_state.event_details = {}

        # Aggiungi un pulsante di refresh
        if st.button("🔄 Refresh Calendario"):
            st.session_state.calendar_needs_update = True

        cal_col, details_col = st.columns([4, 1])

        with cal_col:
            # Filtra i workitem in base al TD Specialist selezionato
            if st.session_state.selected_tdsp_code:
                df_filtered_witems = st.session_state.df_workitems[
                    st.session_state.df_workitems["TDSPID"] == st.session_state.selected_tdsp_code
                ].copy()
            else:
                df_filtered_witems = st.session_state.df_workitems.copy()

            df_filtered_witems['REFDATE'] = pd.to_datetime(df_filtered_witems['REFDATE']).dt.strftime('%Y-%m-%d')

            # Crea gli eventi per il calendario
            calendar_events = []
            st.session_state.event_details = {}  # Reset dei dettagli degli eventi

            for index, row in df_filtered_witems.iterrows():
                tdsp_name = modules.servant.get_description_from_code(st.session_state.df_users, row['TDSPID'], "NAME")
                tdspid = row['TDSPID']
                woid = row['WOID']
                date = row['REFDATE']

                # Crea una chiave univoca per l'evento
                event_key = f"{woid}_{date}_{tdspid}"

                # Salva i dettagli dell'evento nella sessione
                st.session_state.event_details[event_key] = {
                    "woid": woid,
                    "tdspid": tdspid,
                    "tdsp_name": tdsp_name,
                    "status": row['STATUS'],
                    "time_qty": row['TIME_QTY'],
                    "time_um": row.get('TIME_UM', 'H'),
                    "tskgrl1": row.get('TSKGRL1', ''),
                    "tskgrl1_name": modules.servant.get_description_from_code(st.session_state.df_tskgrl1, row.get('TSKGRL1', ''), "NAME"),
                    "tskgrl2": row.get('TSKGRL2', ''),
                    "tskgrl2_name": modules.servant.get_description_from_code(st.session_state.df_tskgrl2, row.get('TSKGRL2', ''), "NAME"),
                    "description": row.get('DESC', ''),
                    "note": row.get('NOTE', ''),
                    "date": date,
                    "index": index
                }

                # Crea l'evento per il calendario
                if row['STATUS'] == "ACTIVE":
                    back_color = '#d4efdf'
                    border_color = '#a2d9ce'
                else:
                    back_color = '#efd4d7'
                    border_color = '#da9ca3'
                
                event = {
                    "id": event_key,
                    "title": f"[{woid}] - {row['TIME_QTY']} H - {tdsp_name}",
                    "start": date,
                    "backgroundColor": back_color,
                    "borderColor": border_color,
                    "display": "block"
                }
                calendar_events.append(event)

            # Opzioni del calendario
            calendar_options = {
                "editable": True,
                "navLinks": True,
                "selectable": True,
                "headerToolbar": {
                    "left": "today prev,next",
                    "center": "title",
                    "right": "dayGridMonth,timeGridWeek"
                },
                "validRange": {
                    "start": f"{first_day_previous_month}",
                    "end": f"{last_day_current_month}"
                },
                "hiddenDays": [0, 6],
                "locale": {
                    "code": "it",
                    "week": {
                        "dow": 1,
                        "doy": 4
                    }
                },
                "timeZone": "Europe/Rome",
                "buttonText": {
                    "today": "Oggi",
                    "month": "Mese",
                    "week": "Settimana"
                },
                'views': {
                    'dayGridMonth': {
                        'buttonText': 'Mese',
                        'dayHeaderFormat': {
                            'weekday': 'short'
                        }
                    },
                    'timeGridWeek': {
                        'buttonText': 'Settimana',
                        'allDaySlot': True,
                        'dayHeaderFormat': {
                            'weekday': 'short',
                            'day': '2-digit',
                            'month': '2-digit',
                        },
                        'slotLabelFormat': {
                            'hour': '',
                            'minute': ''
                        },
                        'height': 300,
                        'slotMinTime': '00:00:00',
                        'slotMaxTime': '00:00:00'
                    }
                }
            }

            # CSS personalizzato
            custom_css = """
                .fc-event-past {
                    opacity: 0.8;
                }
                .fc-event-time {
                    font-style: italic;
                }
                .fc-event-title {
                    font-weight: 700;
                    color: #000000;
                    white-space: pre-wrap;
                    cursor: pointer;
                }
                .fc-toolbar-title {
                    font-size: 2rem;
                }
                .fc-daygrid-day.fc-day-other {
                    display: none;
                }
                .fc-col-header-cell {
                    background-color: #DAF7A6 !important;
                    color: #000000;
                }
                .fc-timegrid-slot-lane {
                    display: none;
                }
                .fc-timegrid-slot-label {
                    display: none;
                }
            """

            # Mostra il calendario
            if st.session_state.calendar_needs_update:
                with st.spinner("Aggiornamento calendario..."):
                    # Ricarica i dati dal database
                    st.session_state.df_workitems = modules.sqlite_db.load_workitems_data(conn)
                    st.session_state.calendar_needs_update = False  # Reset del flag

                    # Rigenera il calendario
                    calendar_output = calendar(
                        events=calendar_events,
                        options=calendar_options,
                        custom_css=custom_css,
                        key=f'calendar_{st.session_state.selected_tdsp_code or "all"}'
                    )
            else:
                calendar_output = calendar(
                    events=calendar_events,
                    options=calendar_options,
                    custom_css=custom_css,
                    key=f'calendar_{st.session_state.selected_tdsp_code or "all"}'
                )

            # Gestione del click sull'evento
            if calendar_output.get("eventClick"):
                event_key = calendar_output["eventClick"]["event"]["id"]
                st.session_state.selected_event_key = event_key

        # Pannello dei dettagli a destra
        with details_col:
            if hasattr(st.session_state, 'selected_event_key') and st.session_state.selected_event_key is not None:
                event_key = st.session_state.selected_event_key
                if event_key in st.session_state.event_details:
                    event_data = st.session_state.event_details[event_key]

                    with st.form(key=f"edit_form_{event_key}"):
                        st.markdown("#### _Modifica Workitem_")
                        st.markdown(f"**Work Order ID:** {event_data['woid']}")
                        if event_data['status'] == 'ACTIVE':
                            st.markdown(f"**Status:** :green-background[{event_data['status']}]")
                        else:
                            st.markdown(f"**Status:** :red-background[{event_data['status']}]")   
                        st.markdown(f"**Specialist:** {event_data['tdsp_name']}")
                        st.markdown(f"**Data:** {event_data['date']}")

                        # Campi modificabili
                        new_time_qty = st.number_input(
                            ":blue[Time]",
                            min_value=0.0,
                            max_value=24.0,
                            value=float(event_data['time_qty']),
                            step=0.5,
                            format="%.1f"
                        )

                        new_description = st.text_area(
                            ":blue[Description]",
                            value=event_data['description'],
                            height=100
                        )

                        new_note = st.text_area(
                            ":blue[Note]",
                            value=event_data['note'],
                            height=100
                        )

                        # Pulsanti Save e Delete
                        col1, col2 = st.columns(2)
                        with col1:
                            save_submitted = st.form_submit_button("Save")
                        with col2:
                            delete_submitted = st.form_submit_button("Delete")

                        if save_submitted:
                            try:
                                # Aggiorna il DataFrame originale
                                df_index = event_data['index']
                                st.session_state.df_workitems.at[df_index, 'TIME_QTY'] = new_time_qty
                                st.session_state.df_workitems.at[df_index, 'DESC'] = new_description
                                st.session_state.df_workitems.at[df_index, 'NOTE'] = new_note

                                # Prepara il dizionario per l'aggiornamento
                                workitem_dict = {
                                    "REFDATE": event_data['date'],
                                    "WOID": event_data['woid'],
                                    "TDSPID": event_data['tdspid'],
                                    "STATUS": "ACTIVE",
                                    "TSKGRL1": event_data['tskgrl1'],
                                    "TSKGRL2": event_data['tskgrl2'],
                                    "TIME_QTY": new_time_qty,
                                    "TIME_UM": "H",
                                    "DESCRIPTION": new_description,
                                    "NOTE": new_note
                                }
                                st.write(workitem_dict)
                                # Aggiorna il database
                                rc = modules.sqlite_db.save_workitem(workitem_dict, conn)
                                st.success("Update successfully!")

                                st.session_state.calendar_needs_update = True
                                st.session_state.selected_event_key = None  # Imposta esplicitamente a None
                                if 'selected_event_key' in st.session_state: # Forse non serve più, ma per sicurezza
                                    del st.session_state.selected_event_key
                                if 'event_details' in st.session_state:
                                    del st.session_state.event_details
                                    st.write("Rerunning after save") # Debug print    

                                # Forza il refresh del calendario
                                st.session_state.df_workitems = modules.sqlite_db.load_workitems_data(conn)
                                time.sleep(0.1)
                                st.rerun()

                            except Exception as e:
                                st.error(f"ERROR saving workitem data: {str(e)}")
        
                        if delete_submitted:
                            try:
                                # Prepara il dizionario per la cancellazione
                                workitem_dict = {
                                    "REFDATE": event_data['date'],
                                    "WOID": event_data['woid'],
                                    "TDSPID": event_data['tdspid'],
                                    "STATUS": "DELETED",
                                    "TSKGRL1": event_data['tskgrl1'],
                                    "TSKGRL2": event_data['tskgrl2'],
                                    "TIME_QTY": new_time_qty,
                                    "TIME_UM": "H",
                                    "DESCRIPTION": new_description,
                                    "NOTE": new_note
                                }

                                # Cancella l'evento dal database
                                rc = modules.sqlite_db.save_workitem(workitem_dict, conn)
                                st.success("Work item deleted successfully!")

                                # Aggiorna lo stato della sessione
                                st.session_state.calendar_needs_update = True
                                st.session_state.selected_event_key = None  # Imposta esplicitamente a None
                                if 'selected_event_key' in st.session_state:  # Forse non serve più, ma per sicurezza
                                    del st.session_state.selected_event_key
                                if 'event_details' in st.session_state:
                                    del st.session_state.event_details

                                # Forza il refresh del calendario
                                st.session_state.df_workitems = modules.sqlite_db.load_workitems_data(conn)
                                time.sleep(0.1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"ERROR deleting workitem data: {str(e)}")
        
        return calendar_output


    # Load data only once and store in session state
    modules.sqlite_db.initialize_session_state(conn)

    previus_xdays = datetime.now() - timedelta(days=10)
    previus_xdays = previus_xdays.date()


    if "df_out" not in st.session_state:
        # Converti la colonna in datetime, gestendo eventuali errori
        st.session_state.df_workitems["REFDATE"] = pd.to_datetime(st.session_state.df_workitems["REFDATE"], errors='coerce')
        
        # Verifica la presenza di valori NaT
        if st.session_state.df_workitems["REFDATE"].isna().sum() > 0:
            print("Attenzione: ci sono valori non convertibili nella colonna REFDATE")
        
        # Filtra i dati
        st.session_state.df_out = st.session_state.df_workitems[
            st.session_state.df_workitems["REFDATE"].dt.date > previus_xdays
        ].copy()


    # Reload workitems if needed
    if 'reload_needed' in st.session_state and st.session_state.reload_needed:
        st.session_state.df_workitems = modules.sqlite_db.load_workitems_data(conn)
        st.session_state.df_out = st.session_state.df_workitems[st.session_state.df_workitems["REFDATE"].dt.date > previus_xdays].copy()
        del st.session_state.reload_needed

    tdsp_woassignedto_names_df = st.session_state.df_users[st.session_state.df_users["DEPTCODE"]=="DTD"]["NAME"]
    tdsp_woassignedto_names_list = list(tdsp_woassignedto_names_df)
    tdsp_woassignedto_names = sorted(tdsp_woassignedto_names_list)


    selected_tdsp_name = st.sidebar.selectbox(
        label=":blue[Tech Dept Specialist]",
        options=tdsp_woassignedto_names,
        index=None,
        key="tdsp_sidebar"
    )

    # Store selected_tdsp_code in session state for consistency
    if selected_tdsp_name:
        selected_tdsp_code = st.session_state.df_users[st.session_state.df_users["NAME"] == selected_tdsp_name]["CODE"].iloc[0]
        st.session_state.selected_tdsp_code = selected_tdsp_code  # Store in session state
    else:
        st.session_state.selected_tdsp_code = None


    # Filter workitems based on the stored code in session state
    if st.session_state.selected_tdsp_code:
        filtered_workitems = st.session_state.df_workitems[
            st.session_state.df_workitems["TDSPID"] == st.session_state.selected_tdsp_code
        ].copy()  # .copy() is crucial here as well
    else:
        filtered_workitems = st.session_state.df_workitems.copy() #.copy() is crucial here as well
    
    filtered_workitems = filtered_workitems.sort_values(['REFDATE','TDSPID','WOID'], ascending=[False, True, True])
    

    st.session_state.df_out = pd.DataFrame(filtered_workitems)  # No need to drop columns here

    # Reset form fields if needed
    if 'form_reset' in st.session_state and st.session_state.form_reset:
        #st.session_state.tdsp_form = st.session_state.tdsp_sidebar
        st.session_state.tdsp_form = st.session_state.selected_tdsp_code
        st.session_state.sb_wo = None
        st.session_state.sb_tskgrl1 = None
        st.session_state.sb_tskgrl2 = None
        st.session_state.in_time_qty = 0.0
        st.session_state.ti_description = ""
        st.session_state.ta_note = ""
        del st.session_state.form_reset
    
    #show_workitem_dataframe()
    calendar_output = show_calendar()
    
    #st.write(selected_tdsp_name)
    #st.write(calendar_output) 
    if calendar_output.get("callback") == "dateClick":
        d = calendar_output.get("dateClick")
        date_iso = d.get("date")
        # 1. Converti la stringa in un oggetto datetime
        data_datetime = datetime.fromisoformat(date_iso.replace("Z", "+00:00"))

        # 2. Formatta l'oggetto datetime nel formato desiderato
        formatted_date = data_datetime.strftime("%Y-%m-%d")
        #st.write(formatted_date)
    else:
        st.write(f"Pick a day from calendar first!")
        formatted_date = datetime.now().strftime("%Y-%m-%d")    
    
    if selected_tdsp_name:
        with st.expander(label=":orange[New Workitem]", expanded=False):
            if selected_tdsp_name:
                # Verifica se selected_tdsp_name è nella lista
                if selected_tdsp_name in tdsp_woassignedto_names:
                    tdsp_index = tdsp_woassignedto_names.index(selected_tdsp_name)
                    selected_tdsp_code = modules.servant.get_code_from_name(st.session_state.df_users, selected_tdsp_name, "CODE")
                else:
                    # Gestisci il caso in cui selected_tdsp_name non è nella lista
                    tdsp_index = 0  # o un altro valore predefinito

                selected_td_specialist_form = st.selectbox(
                    label=":blue[TD Specialist](:red[*])",
                    options=tdsp_woassignedto_names,
                    index=tdsp_index
                )
            else:
                # Gestisci il caso in cui selected_tdsp_name è None o vuoto
                selected_td_specialist_form = st.selectbox(
                    label=":blue[TD Specialist](:red[*])",
                    options=tdsp_woassignedto_names,
                    index=0  # o un altro valore predefinito
                )
                selected_tdsp_code = modules.servant.get_code_from_name(st.session_state.df_users, selected_td_specialist_form, "CODE")



            # Correctly filter and extract Work Order IDs
            filtered_workorder_df = st.session_state.df_woassignedto[
                st.session_state.df_woassignedto["TDSPID"] == selected_tdsp_code
            ]

            if not filtered_workorder_df.empty:  # Check if the DataFrame is not empty
                filtered_workorder_list = sorted(filtered_workorder_df["WOID"].tolist())  # Extract WOIDs and convert to a sorted list
            else:
                filtered_workorder_list = []  # Handle the case where no work orders are found            
            
            wa_linked = st.toggle("Referred to Work Activiy")
            if wa_linked:
                filtered_workorder_df = filtered_workorder_df[
                    (filtered_workorder_df["WOID"] == st.session_state.df_wo_activity["WOID"])
                    ]
                if not filtered_workorder_df.empty:  # Check if the DataFrame is not empty
                    filtered_workorder_list = sorted(filtered_workorder_df["WOID"].tolist())  # Extract WOIDs and convert to a sorted list
                else:
                    filtered_workorder_list = []  # Handle the case where no work orders are found 

            selected_workorder = st.selectbox(
                label=":blue[Work Order]",
                options=filtered_workorder_list,
                index=None,
                key="sb_wo"
                )

            # Task Group Level 1 dropdown
            tskgrl1_options = st.session_state.df_tskgrl1["NAME"].tolist()
            selected_tskgrl1 = st.selectbox(
                label=":blue[TaskGroup L1]", 
                options=tskgrl1_options, 
                index=None, 
                key="sb_tskgrl1"
            )
            selected_tskgrl1_code = modules.servant.get_code_from_name(st.session_state.df_tskgrl1, selected_tskgrl1, "CODE")

            # Task Group Level 2 dropdown (dependent on Level 1)
            tskgrl2_options = st.session_state.df_tskgrl2[st.session_state.df_tskgrl2['PCODE'] == selected_tskgrl1_code]['NAME'].unique()
            selected_tskgrl2 = st.selectbox(
                label=":blue[TaskGroup L2]", 
                options=tskgrl2_options, 
                index=None, 
                key="sb_tskgrl2"
            )
            selected_tskgrl2_code = modules.servant.get_code_from_name(st.session_state.df_tskgrl2, selected_tskgrl2, "CODE")

            # Execution Date
            if formatted_date:
                #st.write(formatted_date)
                default_date_str = formatted_date
                default_date = date.fromisoformat(default_date_str) #Convert to date object
                #st.write(default_date)
        
            execution_date = st.date_input(label=":blue[Execution Date]", value=default_date, format="DD/MM/YYYY")

            # Quantity
            quantity = st.number_input(label=":blue[Time]", min_value=0.0, step=0.5, value=0.0, key="in_time_qty")

            # Description
            desc = st.text_input(label=":blue[Description]", key="ti_description")

            # Note
            note = st.text_area(label=":blue[Notes]", key="ta_note")

            save_button_disabled = not all([  # Use all() for cleaner logic
                execution_date,
                selected_tdsp_code,
                selected_workorder,
                selected_tskgrl1_code,
                selected_tskgrl2_code,
                quantity
            ])

            if st.button("Save Work Item", disabled=save_button_disabled):
                witem = {
                    "REFDATE": execution_date,
                    "WOID": selected_workorder,
                    "TDSPID": selected_tdsp_code,
                    "STATUS": "ACTIVE",
                    "TSKGRL1": selected_tskgrl1_code,
                    "TSKGRL2": selected_tskgrl2_code,
                    "DESCRIPTION": desc,
                    "NOTE": note,
                    "TIME_QTY": quantity,
                    "TIME_UM": "H"
                }

                success = modules.sqlite_db.save_workitem(witem, conn)
                if success:
                    st.success("New workitem created!")

                    # Imposta il flag per aggiornare il calendario
                    st.session_state.calendar_needs_update = True
                    
                    # Imposta il flag per ricaricare i dati
                    st.session_state.reload_needed = True
                    
                    # Resetta i campi del form
                    st.session_state.form_reset = True
                    
                    # Forza il riavvio della pagina
                    time.sleep(1)  # Breve pausa per mostrare il messaggio di successo
                    st.rerun()

            
def main():
    pass

if __name__ == "__main__":
    main()
else:
    create_workitem(st.session_state.conn) 