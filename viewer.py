"""Exploration rapide du stockage LanceDB (nécessite streamlit : pip install streamlit)."""

import os

import streamlit as st

try:
    import lancedb
except ImportError:
    st.error("Installez lancedb : pip install lancedb")
    st.stop()

from config import LANCE_DB_PATH, LANCE_TABLE_NAME

st.title("LanceDB — aperçu de l'index")

if not os.path.isdir(LANCE_DB_PATH):
    st.warning(f"Dossier inexistant : {LANCE_DB_PATH}")
    st.stop()

db = lancedb.connect(LANCE_DB_PATH)
tables = db.table_names()
st.write("Tables :", tables)

if LANCE_TABLE_NAME not in tables:
    st.warning(f"Table « {LANCE_TABLE_NAME} » absente. Lancez d'abord l'indexation.")
    st.stop()

tbl = db.open_table(LANCE_TABLE_NAME)
st.subheader(LANCE_TABLE_NAME)
arrow = tbl.to_arrow()
n = min(50, arrow.num_rows)
st.dataframe(arrow.slice(0, n).to_pandas())
