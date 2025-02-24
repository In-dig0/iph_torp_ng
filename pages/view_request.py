# 3th party packages
import streamlit as st
import pandas as pd
# Built-in packages
import re
import os
import time
# App modules
import modules.sqlite_db
import modules.servant


def view_requests(conn) -> None:

    # Inzialise variables
    rc = 0
    req_nr = ""

    def reset_application_state():
        """Reset all session state variables and cached data"""
        
        if 'grid_response' not in st.session_state:
            st.session_state['grid_response'] = None

        #Reload request data into df
        st.session_state['df_requests'] = modules.sqlite_db.load_requests_data(conn)
        
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
        # Reset the grid response to remove any selected rows 
        st.session_state['grid_response'] = None
        # Forza il rerun dell'applicazione        
        st.rerun()

    modules.sqlite_db.initialize_session_state(conn)
    df_requests_grid = pd.DataFrame()

    # Aggiungere all'inizio della funzione assign_request(), dopo le altre inizializzazioni
    if "grid_refresh" not in st.session_state:
        st.session_state.grid_refresh = False

    df_requests_grid['REQID'] = st.session_state.df_requests['REQID']
    df_requests_grid['STATUS'] = st.session_state.df_requests['STATUS']
    df_requests_grid['INSDATE'] = st.session_state.df_requests['INSDATE']#.dt.strftime('%d/%m/%Y')
    df_requests_grid['DUEDATE'] = st.session_state.df_requests['DUEDATE']
#    df_requests_grid['DEPTNAME'] = df_requests['DEPT'].apply(lambda dept_code: get_description_from_code(df_depts, dept_code, "NAME"))
    df_requests_grid['PRIORITY'] = st.session_state.df_requests['PRIORITY']
    df_requests_grid['PRLINE_NAME'] = st.session_state.df_requests['PR_LINE'].apply(lambda pline_code: modules.servant.get_description_from_code(st.session_state.df_pline, pline_code, "NAME"))
    df_requests_grid['TITLE'] = st.session_state.df_requests['TITLE']
    df_requests_grid['REQUESTER_NAME'] = st.session_state.df_requests['REQUESTER'].apply(lambda requester_code: modules.servant.get_description_from_code(st.session_state.df_users, requester_code, "NAME"))


    if st.session_state.grid_refresh:
        st.session_state.grid_data = df_requests_grid.copy()
        st.session_state.grid_refresh = False    


    # Inizializzazione della sessione
    if "grid_data" not in st.session_state:
        st.session_state.grid_data = df_requests_grid.copy()  # Copia per evitare modifiche al DataFrame originale
    if "grid_response" not in st.session_state:
        st.session_state.grid_response = None

    # Sidebar controls - Filters
    st.sidebar.header("Filters")

    # Creation of a filter REQUESTERNAME
    ct_requester = df_requests_grid['REQUESTER_NAME'].drop_duplicates().sort_values()
    df_requestername = st.session_state.df_users[st.session_state.df_users["CODE"].isin(ct_requester)]
    option_requestername = df_requestername['NAME'].sort_values()
    option_requestername_list = ct_requester.tolist()

    # Get an optional value requester filter
    requestername_filter = st.sidebar.selectbox("Select a Requester Name:", option_requestername_list, index=None)
   

    # Filtro e AGGIORNAMENTO DEI DATI (utilizzando la sessione)
    if requestername_filter:
        st.session_state.grid_data = df_requests_grid.loc[df_requests_grid["REQUESTER_NAME"] == requestername_filter].copy()
    else:
        st.session_state.grid_data = df_requests_grid.copy() # Mostra tutti i dati se il filtro è None

    st.subheader(":orange[Request list]") 
    # Creazione/Aggiornamento della griglia (UNA SOLA VOLTA per ciclo di esecuzione)
    with st.container(border=True):
        st.session_state.grid_response = modules.servant.create_grid(st.session_state.grid_data, "main_grid")
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("Refresh", type="primary", icon=":material/refresh:"):
                reset_application_state()
   
    selected_row = st.session_state.grid_response['selected_rows']

    if selected_row is not None and len(selected_row) > 0:
        reqid = selected_row['REQID'].iloc[0]
        insdate = selected_row['INSDATE'].iloc[0]
        duedate = selected_row['DUEDATE'].iloc[0]
        status = selected_row['STATUS'].iloc[0]
        requester_name = selected_row['REQUESTER_NAME'].iloc[0]
        pline_name = selected_row['PRLINE_NAME'].iloc[0]

        dept_code = st.session_state.df_requests[st.session_state.df_requests["REQID"] == reqid]["DEPT"].values[0]
        dept_name = modules.servant.get_description_from_code(st.session_state.df_depts, dept_code, "NAME")

        family_code = st.session_state.df_requests[st.session_state.df_requests["REQID"] == reqid]["PR_FAMILY"].values[0]
        family_name = modules.servant.get_description_from_code(st.session_state.df_pfamily, family_code, "NAME")

        type_code = st.session_state.df_requests[st.session_state.df_requests["REQID"] == reqid]["TYPE"].values[0]
        type_name = modules.servant.get_description_from_code(st.session_state.df_type, type_code, "NAME")
        
        category_code = st.session_state.df_requests[st.session_state.df_requests["REQID"] == reqid]["CATEGORY"].values[0]
        category_name = modules.servant.get_description_from_code(st.session_state.df_category, category_code, "NAME")

        detail_code = st.session_state.df_requests[st.session_state.df_requests["REQID"] == reqid]["DETAIL"].values[0]
        detail_name = modules.servant.get_description_from_code(st.session_state.df_detail, detail_code, "NAME")

        title = selected_row['TITLE'].iloc[0]
        description = st.session_state.df_requests[st.session_state.df_requests["REQID"] == reqid]["DESCRIPTION"].values[0]
        note_td = st.session_state.df_requests[st.session_state.df_requests["REQID"] == reqid]["NOTE_TD"].values[0]

        tdtl_code_list = st.session_state.df_reqassignedto[st.session_state.df_reqassignedto["REQID"] == reqid]["TDTLID"]
        #tdtl_name_list = get_description_from_code(df_users, tdtl_code_list, "NAME")
        tdtl_name_list = [modules.servant.get_description_from_code(st.session_state.df_users, code, "NAME") for code in tdtl_code_list]
        tdtl_name_string = "-".join(tdtl_name_list)

        attachments= st.session_state.df_attachments[st.session_state.df_attachments["REQID"] == reqid]["TITLE"]
        attachments_list = attachments.tolist()
        attachments_string = "-".join(attachments_list)        

        data_out = {
            "Column name": [
                "Request Id", 
                "Insert date",
                "Desired due date",
                "Status", 
                "Department", 
                "Requester", 
                "Product line", 
                "Product family", 
                "Type", 
                "Category", 
                "Detail", 
                "Title", 
                "Description", 
                "TD Team Leader",
                "TD Note", 
                "Attachments"],
            "Column value": [
                reqid, 
                insdate, 
                duedate,
                status, 
                dept_name, 
                requester_name, 
                pline_name, 
                family_name, 
                type_name, 
                category_name, 
                detail_name, 
                title, 
                description,
                tdtl_name_string,                 
                note_td,
                attachments_string]
        }
        

        df_out = pd.DataFrame(data_out)

        # Formattazione Request Id in grassetto
        df_out.loc[df_out["Column name"] == "Request Id", "Column value"] = df_out.loc[
            df_out["Column name"] == "Request Id", "Column value"].apply(lambda x: f"<b>{x}</b>")

        # Formattazione Status in verde
        df_out.loc[df_out["Column name"] == "Status", "Column value"] = df_out.loc[
            df_out["Column name"] == "Status", "Column value"].apply(lambda x: f"<span style='color: green;'>{x}</span>")
      
        # Convertiamo il DataFrame in HTML con testo allineato a sinistra e senza id riga
        html_table = df_out.to_html(escape=False, index=False, table_id='styled-table')

        # CSS per lo stile della tabella e adattamento delle larghezze delle colonne
        st.markdown("""
            <style>
                #styled-table {
                    width: 100%;
                    text-align: left;
                    border-collapse: collapse;
                }
                #styled-table th:nth-child(1), #styled-table td:nth-child(1) {
                    text-align: left;
                    width: 30%;
                    padding: 6px;
                }
                #styled-table th:nth-child(2), #styled-table td:nth-child(2) {
                    text-align: left;
                    width: 70%;
                    padding: 6px;
                }
                #styled-table th, #styled-table td {
                    padding: 4px;
                }
                #styled-table th, #styled-table thead tr {
                    background-color: #f5f5f5 ;
                }

            </style>
            """, unsafe_allow_html=True)
            
        st.subheader(":orange[Request details]")
        with st.container(border=True):
            st.write(html_table, unsafe_allow_html=True)

            # Creiamo una versione formattata per la visualizzazione
            def format_cell(col_name, value):
                if col_name == 'Request Id':
                    return f"**{value}**"
                elif col_name == 'Status':
                    return f":green[{value}]"
                return value

            # Applica la formattazione per la visualizzazione Streamlit
            df_display = df_out.copy()
            for idx, row in df_out.iterrows():
                df_display.at[idx, 'Column value'] = format_cell(row['Column name'], row['Column value'])

            #st.dataframe(df_display, hide_index=True)

            # Aggiungi il pulsante di download
            file_name = f"{reqid}_details.pdf"
            pdf_buffer = modules.servant.create_pdf_buffer(df_out)
            st.download_button(
                label="Download PDF",
                data=pdf_buffer,
                file_name=file_name,
                mime="application/pdf",
                key="download-pdf",
                help="Click qui per scaricare la tabella in formato PDF",
                type="primary",
                icon=":material/download:"
            )
                    # REQUEST ATTACHMENT SECTION
        if attachments_string :
            st.subheader(":orange[Attachments]")        
            with st.container(border=True):
                modules.sqlite_db.view_attachments(reqid, conn)
  

def main():
    pass

if __name__ == "__main__":
    main()
else:
    view_requests(st.session_state.conn)