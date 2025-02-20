import streamlit as st
import pandas as pd
import modules.sqlite_db
from datetime import datetime
import time
from typing import Optional, Tuple, Dict, List
import io
import re
import os
import hmac
import pathlib
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT
#from reportlab.pdfgen import canvas


def get_code_from_name(df, name, code_column):
    result = df[df["NAME"] == name][code_column]
    return list(result)[0] if not result.empty else ""


def get_description_from_code(df, code, description_column):
    result = df[df["CODE"] == code][description_column]
    return list(result)[0] if not result.empty else ""


def remove_html_tags(text):
    """Rimuove i tag HTML da una stringa, ignorando eventuali valori None."""
    if text is None:
        return ""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


def convert_df(df):
    df_clean = df.copy()
    df_clean["Column value"] = df_clean["Column value"].apply(remove_html_tags)
    return df_clean.to_csv(index=False, sep=';').encode('utf-8')


def clean_html_tags(text):
    """Rimuove i tag HTML dal testo"""
    if isinstance(text, str):
        # Rimuove i tag <b> e </b>
        text = re.sub(r'</?b>', '', text)
        # Rimuove i tag span con stile
        text = re.sub(r'<span[^>]*>', '', text)
        text = re.sub(r'</span>', '', text)
    return text


def create_pdf_buffer(df):
    """
    Crea un buffer PDF contenente la tabella formattata
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    # Aggiungi il titolo "Richiesta UT"
    styles = getSampleStyleSheet()
    title = Paragraph("Technic Department Request", styles['Title'])
    elements.append(title)
  
    elements.append(Spacer(1, 12))
    
    # Pulisci i dati dai tag HTML per il PDF
    df_clean = df.copy()
    df_clean['Column value'] = df_clean['Column value'].apply(clean_html_tags)
    
    # Converti DataFrame in lista di liste per la tabella
    data = [df_clean.columns.tolist()] + df_clean.values.tolist()
    
    # Calcola la larghezza disponibile per la tabella
    page_width = doc.width
    col1_width = page_width * 1 / 4  # 1/4 della larghezza per "Column name"
    col2_width = page_width * 3 / 4  # 3/4 della larghezza per "Column value"
    
    # Crea e stila la tabella
    table = Table(data, colWidths=[col1_width, col2_width])  # Imposta larghezze specifiche

    table.setStyle(TableStyle([
        # Stile header
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        # Stile celle
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        # Stile speciale per Request Id (bold)
        ('FONTNAME', (1, 1), (1, 1), 'Helvetica-Bold'),
        # Stile speciale per Status (verde)
        ('TEXTCOLOR', (1, 4), (1, 4), colors.green),
    ]))
    
    elements.append(table)
    
        # Aggiungi un po' di spazio tra la data/ora e il titolo
    elements.append(Spacer(1, 24))

    # Aggiungi la data e l'ora di generazione in alto a destra
    styles = getSampleStyleSheet()
    right_align_style = ParagraphStyle(
        name='RightAlign',
        parent=styles['Normal'],
        alignment=TA_RIGHT,
        fontSize=10,
        textColor=colors.black,
    )
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    timestamp = Paragraph(f"Timestamp: {current_time}", right_align_style)
    elements.append(timestamp)


    doc.build(elements)
    buffer.seek(0)
    return buffer

def check_file_existance(path: pathlib) -> bool:
    """ Function tha returns True if a input string is a file and the file exists """    
    if os.path.exists(path) and os.path.isfile(path):
        return True
    else:
        return False    

def check_folder_existance(path: pathlib) -> bool:
    """ Function tha returns True if a input string is a folder and the folder exists """   
    if os.path.exists(path) and os.path.isdir(path):
        return True
    else:
        return False 
