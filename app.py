# app.py
import streamlit as st
import pandas as pd
from io import BytesIO
from pathlib import Path

# ----------------------------
# Konfigurasi / Nama file
# ----------------------------
EXCEL_PATH = Path("ph_debit_data.xlsx")
SHEET_NAMES = ["Power Plant", "Plant Garage", "Drain A", "Drain B", "Drain C"]
COLUMNS = ["tanggal", "bulan", "tahun", "pH", "debit", "ph_rata_rata_bulan"]

st.set_page_config(page_title="Pencatatan pH & Debit Air", layout="centered")

st.title("📊 Pencatatan pH dan Debit Air")

# ----------------------------
# Inisialisasi file Excel bila belum ada
# ----------------------------
def initialize_excel(path: Path):
    # jika file belum ada, buat file dengan sheet kosong untuk setiap lokasi
    if not path.exists():
        writer = pd.ExcelWriter(path, engine="openpyxl")
        for sheet in SHEET_NAMES:
            df = pd.DataFrame(columns=COLUMNS)
            df.to_excel(writer, sheet_name=sheet, index=False)
        writer.close()

initialize_excel(EXCEL_PATH)

# ----------------------------
# Utility: baca sheet, simpan semua sheet
# ----------------------------
def read_all_sheets(path: Path):
    # membaca semua sheet ke dict {sheetname: DataFrame}
    return pd.read_excel(path, sheet_name=None, engine="openpyxl")

def save_all_sheets(dfs: dict, path: Path):
    with pd.ExcelWriter(path, engine="xlsxwriter", datetime_format="yyyy-mm-dd") as writer:  # <-- ganti engine
        for sheet, df in dfs.items():
            # pastikan kolom urut sesuai COLUMNS
            df = df.reindex(columns=COLUMNS)

            # Tambahkan kolom tanggal lengkap
            df["tanggal_lengkap"] = pd.to_datetime(dict(year=df["tahun"], month=df["bulan"], day=df["tanggal"]), errors='coerce')  # <-- ditambahkan

            # Tulis ke Excel
            df.to_excel(writer, sheet_name=sheet, index=False)

            # Format tampilan kolom di Excel
            workbook = writer.book
            worksheet = writer.sheets[sheet]

            # Atur lebar kolom agar rapi dan tanggal terlihat
            worksheet.set_column("A:A", 6)   # tanggal
            worksheet.set_column("B:B", 6)   # bulan
            worksheet.set_column("C:C", 8)   # tahun
            worksheet.set_column("D:D", 10)  # pH
            worksheet.set_column("E:E", 10)  # debit
            worksheet.set_column("F:F", 18)  # ph_rata_rata_bulan
            worksheet.set_column("G:G", 15, workbook.add_format({'num_format': 'yyyy-mm-dd'}))  # tanggal_lengkap
# ----------------------------
# Form input
# ----------------------------
st.markdown("Isi data pengukuran di bawah ini:")

# tanggal kecil: buat 3 kolom kecil
# Input tanggal dengan 1 kotak date picker
tanggal_input = st.date_input("Tanggal pengukuran:", pd.Timestamp.now())

# Pecah jadi hari, bulan, tahun
tanggal = tanggal_input.day
bulan = tanggal_input.month
tahun = tanggal_input.year

lokasi = st.selectbox("Lokasi pengukuran:", SHEET_NAMES)

ph = st.number_input("pH (mis. 7.2)", min_value=0.0, max_value=14.0, value=7.0, format="%.3f")
debit = st.number_input("Debit (mis. L/detik)", min_value=0.0, value=0.0, format="%.3f")

# tombol submit
if st.button("Simpan data"):
    # load semua sheet
    all_sheets = read_all_sheets(EXCEL_PATH)

    # ambil df sheet sesuai lokasi
    df_loc = all_sheets.get(lokasi, pd.DataFrame(columns=COLUMNS))

    # buat row baru
    new_row = {
        "tanggal": int(tanggal),
        "bulan": int(bulan),
        "tahun": int(tahun),
        "pH": float(ph),
        "debit": float(debit),
        "ph_rata_rata_bulan": None  # akan diisi setelah recompute
    }

    # append
    df_loc = pd.concat([df_loc, pd.DataFrame([new_row])], ignore_index=True)

    # recompute rata2 pH per bulan untuk sheet ini
    # pastikan kolom numeric
    df_loc["pH"] = pd.to_numeric(df_loc["pH"], errors="coerce")
    df_loc["bulan"] = pd.to_numeric(df_loc["bulan"], errors="coerce").astype(int)
    df_loc["tahun"] = pd.to_numeric(df_loc["tahun"], errors="coerce").astype(int)

    # hitung rata-rata pH per tahun+bulan
    df_loc["ph_rata_rata_bulan"] = df_loc.groupby(["tahun", "bulan"])["pH"].transform("mean").round(3)

    # update dict dan simpan semua sheet kembali
    all_sheets[lokasi] = df_loc
    save_all_sheets(all_sheets, EXCEL_PATH)

    st.success(f"Data tersimpan di sheet '{lokasi}' — tanggal {tanggal}/{bulan}/{tahun}")

# ----------------------------
# Tampilkan preview data untuk lokasi dipilih
# ----------------------------
st.markdown("---")
st.subheader("Preview data lokasi")
try:
    all_sheets = read_all_sheets(EXCEL_PATH)
    df_preview = all_sheets.get(lokasi, pd.DataFrame(columns=COLUMNS))
    if df_preview.empty:
        st.info("Belum ada data untuk lokasi ini.")
    else:
        st.dataframe(df_preview.sort_values(["tahun","bulan","tanggal"]).reset_index(drop=True))
        # ----------------------------
# Hapus data berdasarkan tanggal dengan konfirmasi
# ----------------------------
st.markdown("### ❌ Hapus data berdasarkan tanggal")

# Tampilkan pilihan tanggal dari data yang ada
if not df_preview.empty:
    # Ambil tanggal unik dari kolom tanggal
    tanggal_unik = pd.to_datetime(df_preview["tanggal"], errors="coerce").dropna().dt.date.unique()

    if len(tanggal_unik) > 0:
        tanggal_hapus = st.selectbox("Pilih tanggal yang ingin dihapus:", sorted(tanggal_unik))

        # Buat key unik untuk tombol berdasarkan tanggal dan lokasi
        tombol_konfirmasi_key = f"konfirmasi_hapus_{tanggal_hapus}_{lokasi}"

        # Tahap 1: Tombol awal untuk menandai akan hapus
        if st.button("Tandai untuk Dihapus"):
            st.warning(f"⚠ Anda memilih untuk menghapus data tanggal {tanggal_hapus} dari lokasi '{lokasi}'.")
            st.session_state[tombol_konfirmasi_key] = True

        # Tahap 2: Jika sudah ditandai, munculkan tombol konfirmasi
        if st.session_state.get(tombol_konfirmasi_key, False):
            if st.button("✅ Konfirmasi Hapus Sekarang"):
                # Hapus data yang sesuai
                df_filtered = df_preview[pd.to_datetime(df_preview["tanggal"]).dt.date != tanggal_hapus]

                # Simpan ulang
                all_sheets[lokasi] = df_filtered
                save_all_sheets(all_sheets, EXCEL_PATH)

                # Reset status
                st.session_state[tombol_konfirmasi_key] = False

                st.success(f"✅ Data tanggal {tanggal_hapus} dari lokasi '{lokasi}' telah dihapus.")
    else:
        st.info("Tidak ada tanggal valid untuk dihapus.")
else:
    st.info("Tidak ada data untuk dihapus.")
except Exception as e:
    st.error(f"Gagal membaca file Excel: {e}")

# ----------------------------
# Tombol download file Excel gabungan
# ----------------------------
st.markdown("---")
st.subheader("Download file Excel gabungan")
with open(EXCEL_PATH, "rb") as f:
    data_bytes = f.read()

st.download_button(
    label="Download file Excel (semua lokasi)",
    data=data_bytes,
    file_name="ph_debit_data.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.info("File disimpan di server sebagai ph_debit_data.xlsx. Data akan bertahan kecuali file dihapus dari server.")


