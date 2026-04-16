import chromadb
import streamlit as st

client = chromadb.PersistentClient(path="chroma_db")

st.title("ChromaDB Viewer")

collections = client.list_collections()

for col in collections:
    st.subheader(col.name)
    data = client.get_collection(col.name).get()
    st.write(data)