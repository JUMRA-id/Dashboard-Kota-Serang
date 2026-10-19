import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Dashboard Fiskal Kota Serang",
    page_icon="📊",
    layout="wide"
)

URL_DATA = "https://raw.githubusercontent.com/JUMRA-id/Dasboard-Fiscal-Insight-/e6244a0e8ff62982d669f7b07b461cd28c3b5a3b/dataset_fiskal_97_hipoFull%20(2).csv"

@st.cache_data
def load_data():
    df = pd.read_csv(URL_DATA)
    df.columns = df.columns.str.strip()
    df["Tahun"] = df["Tahun"].astype(int)
    return df

df = load_data()

# Filter khusus Kota Serang
df_serang = df[df["Kota"].str.strip().str.lower() == "kota serang"].copy()

if df_serang.empty:
    st.error("Data Kota Serang tidak ditemukan. Periksa penulisan nama kota pada kolom 'Kota'.")
    st.stop()

st.title("📊 Dashboard Fiskal dan Sosial Kota Serang")
st.caption("Dashboard ini menampilkan data fiskal daerah, belanja pembangunan, dan indikator sosial Kota Serang.")

# Sidebar filter tahun
tahun_min = int(df_serang["Tahun"].min())
tahun_max = int(df_serang["Tahun"].max())

with st.sidebar:
    st.header("⚙️ Filter Tahun")
    tahun_awal, tahun_akhir = st.slider(
        "Pilih rentang tahun",
        min_value=tahun_min,
        max_value=tahun_max,
        value=(tahun_min, tahun_max)
    )

df_filter = df_serang[
    (df_serang["Tahun"] >= tahun_awal) &
    (df_serang["Tahun"] <= tahun_akhir)
].sort_values("Tahun")

# KPI utama
st.subheader("📌 Ringkasan Utama")

tahun_terakhir = df_filter["Tahun"].max()
data_terakhir = df_filter[df_filter["Tahun"] == tahun_terakhir].iloc[0]

col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric("PAD", f"{data_terakhir['PAD']:.2f}")
col2.metric("DAU", f"{data_terakhir['DAU_Grant']:.2f}")
col3.metric("DAK Fisik", f"{data_terakhir['DAK_Fisik']:.2f}")
col4.metric("Kemiskinan", f"{data_terakhir['KEMISKINAN']:.2f}%")
col5.metric("Pengangguran", f"{data_terakhir['PENGANGGURAN']:.2f}%")
col6.metric("IPM", f"{data_terakhir['IPM']:.2f}")

st.info(f"KPI di atas menunjukkan kondisi Kota Serang pada tahun {tahun_terakhir}.")

# Tren pendapatan fiskal
st.subheader("💰 Tren Pendapatan Fiskal Daerah")

fig, ax = plt.subplots(figsize=(12, 5))

ax.plot(df_filter["Tahun"], df_filter["PAD"], marker="o", label="PAD")
ax.plot(df_filter["Tahun"], df_filter["DAU_Grant"], marker="o", label="DAU")
ax.plot(df_filter["Tahun"], df_filter["DAK_Fisik"], marker="o", label="DAK Fisik")
ax.plot(df_filter["Tahun"], df_filter["DAK_Nonfisik"], marker="o", label="DAK Nonfisik")
ax.plot(df_filter["Tahun"], df_filter["DBH_PAJAK"], marker="o", label="DBH Pajak")

ax.set_title("Tren Pendapatan Fiskal Kota Serang")
ax.set_xlabel("Tahun")
ax.set_ylabel("Nilai")
ax.legend()
ax.grid(True, alpha=0.3)

st.pyplot(fig)

# Komposisi dana transfer
st.subheader("🏦 Komposisi Dana Transfer Tahun Terakhir")

kolom_transfer = [
    "DBH_PAJAK", "DBH_SDA", "DBH_Lainnya",
    "DAU_Grant", "DAU_Earmark",
    "DAK_Fisik", "DAK_Nonfisik"
]

nilai_transfer = data_terakhir[kolom_transfer].astype(float)

fig2, ax2 = plt.subplots(figsize=(10, 5))

ax2.bar(kolom_transfer, nilai_transfer, color="steelblue")
ax2.set_title(f"Komposisi Dana Transfer Kota Serang Tahun {tahun_terakhir}")
ax2.set_ylabel("Nilai")
ax2.tick_params(axis="x", rotation=45)
ax2.grid(axis="y", alpha=0.3)

st.pyplot(fig2)

# Belanja pembangunan
st.subheader("🏗️ Belanja Pembangunan")

kolom_belanja = [
    "bm_pendidikan", "bm_kesehatan", "bm_perumahan",
    "bm_lingkungan", "bm_ekonomi", "bm_infrastruktur",
    "bm_pariwisata", "bm_perlindungan_sosial"
]

pilihan_belanja = st.multiselect(
    "Pilih indikator belanja",
    kolom_belanja,
    default=[
        "bm_pendidikan",
        "bm_kesehatan",
        "bm_infrastruktur",
        "bm_ekonomi"
    ]
)

if pilihan_belanja:
    fig3, ax3 = plt.subplots(figsize=(12, 5))

    for kolom in pilihan_belanja:
        label = kolom.replace("bm_", "").replace("_", " ").title()
        ax3.plot(df_filter["Tahun"], df_filter[kolom], marker="o", label=label)

    ax3.set_title("Tren Belanja Pembangunan Kota Serang")
    ax3.set_xlabel("Tahun")
    ax3.set_ylabel("Nilai")
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    st.pyplot(fig3)
else:
    st.warning("Pilih minimal satu indikator belanja.")

# Kondisi sosial
st.subheader("👥 Kondisi Sosial Kota Serang")

fig4, ax4 = plt.subplots(figsize=(12, 5))

ax4.plot(df_filter["Tahun"], df_filter["KEMISKINAN"], marker="o", label="Kemiskinan (%)")
ax4.plot(df_filter["Tahun"], df_filter["PENGANGGURAN"], marker="o", label="Pengangguran (%)")
ax4.plot(df_filter["Tahun"], df_filter["KETIMPANGAN"], marker="o", label="Ketimpangan")

ax4.set_title("Tren Indikator Sosial Kota Serang")
ax.set_xlabel("Tahun")
ax4.set_xlabel("Tahun")
ax4.set_ylabel("Nilai")
ax4.legend()
ax4.grid(True, alpha=0.3)

st.pyplot(fig4)

fig5, ax5 = plt.subplots(figsize=(12, 4))

ax5.plot(df_filter["Tahun"], df_filter["IPM"], marker="o", color="green", label="IPM")
ax5.set_title("Tren IPM Kota Serang")
ax5.set_xlabel("Tahun")
ax5.set_ylabel("IPM")
ax5.grid(True, alpha=0.3)

st.pyplot(fig5)

# Statistik deskriptif menggunakan NumPy
st.subheader("🧮 Statistik Deskriptif")

kolom_analisis = [
    "PAD", "DAU_Grant", "DAK_Fisik",
    "KEMISKINAN", "PENGANGGURAN", "IPM"
]

statistik = []

for kolom in kolom_analisis:
    nilai = df_filter[kolom].to_numpy()

    statistik.append({
        "Indikator": kolom,
        "Rata-rata": round(np.mean(nilai), 2),
        "Median": round(np.median(nilai), 2),
        "Minimum": round(np.min(nilai), 2),
        "Maksimum": round(np.max(nilai), 2),
        "Standar Deviasi": round(np.std(nilai), 2)
    })

st.dataframe(pd.DataFrame(statistik), use_container_width=True)

# Tabel data
st.subheader("📋 Data Kota Serang")

st.dataframe(df_filter, use_container_width=True)

st.caption("Sumber data: dataset_fiskal_97_hipoFull (2).csv dari GitHub JUMRA-id/Dasboard-Fiscal-Insight-.")
