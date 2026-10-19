import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Fiscal Insight | Kota Serang",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

URL_DATA = "https://raw.githubusercontent.com/JUMRA-id/Dasboard-Fiscal-Insight-/e6244a0e8ff62982d669f7b07b461cd28c3b5a3b/dataset_fiskal_97_hipoFull%20(2).csv"

WARNA_UTAMA = "#1D4ED8"
WARNA_HIJAU = "#059669"
WARNA_MERAH = "#DC2626"
WARNA_KUNING = "#D97706"
WARNA_UNGU = "#7C3AED"

@st.cache_data
def load_data():
    df = pd.read_csv(URL_DATA)
    df.columns = df.columns.str.strip()
    df["Tahun"] = df["Tahun"].astype(int)
    return df

df = load_data()
df_serang = df[df["Kota"].str.strip().str.lower() == "kota serang"].copy()

if df_serang.empty:
    st.error("Data Kota Serang tidak ditemukan. Periksa penulisan nama kota pada kolom 'Kota'.")
    st.stop()

# CSS agar tampilan lebih menarik
st.markdown("""
<style>
    .main {
        background-color: #F8FAFC;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1 {
        color: #0F172A;
        font-weight: 800;
    }
    .stMetric {
        background: white;
        border-radius: 15px;
        padding: 18px;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
        border-left: 6px solid #1D4ED8;
    }
    .stMetric label {
        color: #64748B;
        font-weight: 600;
    }
    .stMetric div {
        color: #0F172A;
        font-weight: 800;
    }
    div[data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
tahun_min = int(df_serang["Tahun"].min())
tahun_max = int(df_serang["Tahun"].max())

with st.sidebar:
    st.markdown("## 🏙️ Fiscal Insight")
    st.caption("Dashboard Fiskal Kota Serang")

    st.divider()

    st.markdown("### ⚙️ Filter")
    tahun_awal, tahun_akhir = st.slider(
        "Pilih rentang tahun",
        min_value=tahun_min,
        max_value=tahun_max,
        value=(tahun_min, tahun_max)
    )

    st.divider()
    st.markdown("### 📌 Tentang")
    st.info(
        "Dashboard ini menampilkan perkembangan pendapatan fiskal, "
        "belanja pembangunan, dan indikator sosial Kota Serang."
    )

df_filter = df_serang[
    (df_serang["Tahun"] >= tahun_awal) &
    (df_serang["Tahun"] <= tahun_akhir)
].sort_values("Tahun")

tahun_terakhir = df_filter["Tahun"].max()
data_terakhir = df_filter[df_filter["Tahun"] == tahun_terakhir].iloc[0]

# Header
st.markdown(f"""
<div style="
    background: linear-gradient(135deg, #1D4ED8, #7C3AED);
    padding: 28px;
    border-radius: 20px;
    color: white;
    margin-bottom: 25px;
">
    <h1 style="color:white; margin:0;">🏙️ Fiscal Insight Kota Serang</h1>
    <p style="margin:8px 0 0 0; font-size:17px; opacity:0.9;">
        Analisis fiskal daerah, belanja pembangunan, dan kondisi sosial
    </p>
    <p style="margin:10px 0 0 0; font-size:14px; opacity:0.8;">
        Periode data: {tahun_min}–{tahun_max} | Tampil saat ini: {tahun_awal}–{tahun_akhir}
    </p>
</div>
""", unsafe_allow_html=True)

# KPI utama
st.markdown("### 📌 Ringkasan Utama")

col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric("💰 PAD", f"{data_terakhir['PAD']:.2f}")
col2.metric("🏛️ DAU", f"{data_terakhir['DAU_Grant']:.2f}")
col3.metric("🏗️ DAK Fisik", f"{data_terakhir['DAK_Fisik']:.2f}")
col4.metric("📉 Kemiskinan", f"{data_terakhir['KEMISKINAN']:.2f}%")
col5.metric("👷 Pengangguran", f"{data_terakhir['PENGANGGURAN']:.2f}%")
col6.metric("🎓 IPM", f"{data_terakhir['IPM']:.2f}")

st.caption(f"Indikator di atas menunjukkan kondisi Kota Serang pada tahun {tahun_terakhir}.")

# Tren fiskal
st.markdown("### 💰 Tren Pendapatan Fiskal Daerah")

fig, ax = plt.subplots(figsize=(12, 5))

ax.plot(df_filter["Tahun"], df_filter["PAD"], marker="o", linewidth=2.5, color=WARNA_UTAMA, label="PAD")
ax.plot(df_filter["Tahun"], df_filter["DAU_Grant"], marker="o", linewidth=2.5, color=WARNA_HIJAU, label="DAU")
ax.plot(df_filter["Tahun"], df_filter["DAK_Fisik"], marker="o", linewidth=2.5, color=WARNA_KUNING, label="DAK Fisik")
ax.plot(df_filter["Tahun"], df_filter["DAK_Nonfisik"], marker="o", linewidth=2.5, color=WARNA_UNGU, label="DAK Nonfisik")
ax.plot(df_filter["Tahun"], df_filter["DBH_PAJAK"], marker="o", linewidth=2.5, color=WARNA_MERAH, label="DBH Pajak")

ax.set_title("Perkembangan Pendapatan Fiskal Kota Serang", fontsize=14, fontweight="bold")
ax.set_xlabel("Tahun")
ax.set_ylabel("Nilai")
ax.legend(frameon=False)
ax.grid(True, linestyle="--", alpha=0.3)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

st.pyplot(fig, use_container_width=True)

# Komposisi transfer dan belanja
st.markdown("### 🏦 Komposisi Dana Transfer Tahun Terakhir")

kolom_transfer = [
    "DBH_PAJAK", "DBH_SDA", "DBH_Lainnya",
    "DAU_Grant", "DAU_Earmark",
    "DAK_Fisik", "DAK_Nonfisik"
]

nilai_transfer = data_terakhir[kolom_transfer].astype(float)

fig2, ax2 = plt.subplots(figsize=(11, 5))

bars = ax2.bar(kolom_transfer, nilai_transfer, color=WARNA_UTAMA, alpha=0.85)
ax2.set_title(f"Komposisi Dana Transfer Kota Serang Tahun {tahun_terakhir}", fontsize=14, fontweight="bold")
ax2.set_ylabel("Nilai")
ax2.tick_params(axis="x", rotation=45)
ax2.grid(axis="y", linestyle="--", alpha=0.3)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)

for bar in bars:
    tinggi = bar.get_height()
    ax2.text(
        bar.get_x() + bar.get_width() / 2,
        tinggi,
        f"{tinggi:.1f}",
        ha="center",
        va="bottom",
        fontsize=9
    )

st.pyplot(fig2, use_container_width=True)

# Belanja pembangunan
st.markdown("### 🏗️ Belanja Pembangunan")

kolom_belanja = [
    "bm_pendidikan", "bm_kesehatan", "bm_perumahan",
    "bm_lingkungan", "bm_ekonomi", "bm_infrastruktur",
    "bm_pariwisata", "bm_perlindungan_sosial"
]

pilihan_belanja = st.multiselect(
    "Pilih indikator belanja yang ingin ditampilkan",
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

    warna_grafik = [WARNA_UTAMA, WARNA_HIJAU, WARNA_MERAH, WARNA_KUNING, WARNA_UNGU]

    for i, kolom in enumerate(pilihan_belanja):
        label = kolom.replace("bm_", "").replace("_", " ").title()
        ax3.plot(
            df_filter["Tahun"],
            df_filter[kolom],
            marker="o",
            linewidth=2.5,
            color=warna_grafik[i % len(warna_grafik)],
            label=label
        )

    ax3.set_title("Perkembangan Belanja Pembangunan Kota Serang", fontsize=14, fontweight="bold")
    ax3.set_xlabel("Tahun")
    ax3.set_ylabel("Nilai")
    ax3.legend(frameon=False)
    ax3.grid(True, linestyle="--", alpha=0.3)
    ax3.spines["top"].set_visible(False)
    ax3.spines["right"].set_visible(False)

    st.pyplot(fig3, use_container_width=True)
else:
    st.warning("Pilih minimal satu indikator belanja.")

# Kondisi sosial
st.markdown("### 👥 Kondisi Sosial Kota Serang")

col_sosial1, col_sosial2 = st.columns([2, 1])

with col_sosial1:
    fig4, ax4 = plt.subplots(figsize=(10, 5))

    ax4.plot(df_filter["Tahun"], df_filter["KEMISKINAN"], marker="o", linewidth=2.5, color=WARNA_MERAH, label="Kemiskinan (%)")
    ax4.plot(df_filter["Tahun"], df_filter["PENGANGGURAN"], marker="o", linewidth=2.5, color=WARNA_KUNING, label="Pengangguran (%)")
    ax4.plot(df_filter["Tahun"], df_filter["KETIMPANGAN"], marker="o", linewidth=2.5, color=WARNA_UNGU, label="Ketimpangan")

    ax4.set_title("Tren Indikator Sosial", fontsize=14, fontweight="bold")
    ax4.set_xlabel("Tahun")
    ax4.set_ylabel("Nilai")
    ax4.legend(frameon=False)
    ax4.grid(True, linestyle="--", alpha=0.3)
    ax4.spines["top"].set_visible(False)
    ax4.spines["right"].set_visible(False)

    st.pyplot(fig4, use_container_width=True)

with col_sosial2:
    fig5, ax5 = plt.subplots(figsize=(6, 5))

    ax5.plot(df_filter["Tahun"], df_filter["IPM"], marker="o", linewidth=3, color=WARNA_HIJAU)
    ax5.fill_between(df_filter["Tahun"], df_filter["IPM"], alpha=0.15, color=WARNA_HIJAU)

    ax5.set_title("Perkembangan IPM", fontsize=14, fontweight="bold")
    ax5.set_xlabel("Tahun")
    ax5.set_ylabel("IPM")
    ax5.grid(True, linestyle="--", alpha=0.3)
    ax5.spines["top"].set_visible(False)
    ax5.spines["right"].set_visible(False)

    st.pyplot(fig5, use_container_width=True)

# Statistik deskriptif
st.markdown("### 🧮 Statistik Deskriptif")

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

st.dataframe(
    pd.DataFrame(statistik),
    use_container_width=True,
    hide_index=True
)

# Tabel data
with st.expander("📋 Lihat Data Kota Serang"):
    st.dataframe(df_filter, use_container_width=True)

st.divider()
st.caption("Sumber data: dataset_fiskal_97_hipoFull (2).csv dari GitHub JUMRA-id/Dasboard-Fiscal-Insight-. Dibuat menggunakan Streamlit, Pandas, NumPy, dan Matplotlib.")
