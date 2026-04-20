import streamlit as st
import lancedb
from pathlib import Path
from config import LANCE_DB_PATH, LANCE_TABLE_NAME
   
st.set_page_config(page_title="LanceDB Reader", layout="wide")
st.title("📂 LanceDB Reader")

db_path = Path(LANCE_DB_PATH)

if not db_path.exists():
    st.error(f"Le dossier n'existe pas : {db_path}")
    st.stop()

try:
    # ✅ Connexion au même niveau que vectorstore.py
    conn = lancedb.connect(str(db_path))

    # ✅ table_names() comme dans vectorstore.py (pas list_tables())
    tables = conn.table_names()

    st.write("Tables trouvées :", tables)

    if not tables:
        st.warning("Aucune table trouvée dans LanceDB.")
        st.stop()

    table_name = st.selectbox("Choisir une table", options=tables, index=0)
    st.success(f"✅ Table sélectionnée : {table_name}")

    table = conn.open_table(table_name)
    df = table.to_pandas()

    st.subheader(f"📄 Contenu — {len(df)} lignes")
    st.dataframe(df, use_container_width=True)

    st.subheader("🗂️ Colonnes")
    st.write(list(df.columns))

except Exception as e:
    st.error(f"Erreur : {str(e)}") #streamlit run LanceDbReader.py