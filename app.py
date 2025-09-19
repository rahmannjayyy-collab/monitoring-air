import os
os.environ["STREAMLIT_RUNTIME_HOME"] = "/data/.streamlit"
os.environ["STREAMLIT_CONFIG_FILE"] = "/data/.streamlit/config.toml"
import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

# Inisialisasi data
if "data" not in st.session_state:
    st.session_state["data"] = pd.DataFrame(columns=["Tanggal", "Lokasi", "pH", "Debit (L/detik)"])

st.title("📊 Pencatatan pH dan Debit Air")

# Form input
with st.form("input_form"):
    tanggal = st.date_input("Tanggal", datetime.today())
    lokasi = st.selectbox("Lokasi", ["Tempat 1", "Tempat 2", "Tempat 3", "Tempat 4", "Tempat 5"])
    ph = st.number_input("Nilai pH", min_value=0.0, max_value=14.0, step=0.1)
    debit = st.number_input("Debit (L/detik)", min_value=0.0, step=0.1)

    submit = st.form_submit_button("Simpan Data")

# Simpan data
if submit:
    new_data = pd.DataFrame([[tanggal, lokasi, ph, debit]], columns=st.session_state["data"].columns)
    st.session_state["data"] = pd.concat([st.session_state["data"], new_data], ignore_index=True)
    st.success("✅ Data berhasil disimpan!")

# Tampilkan tabel
st.subheader("📑 Data Pencatatan")
st.dataframe(st.session_state["data"], use_container_width=True)

# Fungsi export ke Excel
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Data")
    return output.getvalue()

excel_file = to_excel(st.session_state["data"])

# Tombol download
st.download_button(
    label="⬇ Download Excel",
    data=excel_file,
    file_name="data_ph_debit.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

)
