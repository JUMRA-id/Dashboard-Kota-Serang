import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Dashboard Kota Serang",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

URL_DATA = "https://raw.githubusercontent.com/JUMRA-id/Dashboard-Kota-Serang/8569ca8be3dab3b794ac46862ad5846df906c90c/dataset_fiskal_97_hipoFull.csv"

BIRU = "#2563EB"
HIJAU = "#059669"
MERAH = "#DC2626"
KUNING = "#D97706"
UNGU = "#7C3AED"

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

# Tampilan CSS
st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        color: #0F172A;
    }
    .stMetric {
        background-color: #FFFFFF;
        border-radius: 16px;
        padding: 18px;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.08);
        border-left: 6px solid #2563EB;
    }
    .stMetric label {
        color: #64748B;
        font-weight: 600;
    }
    .stMetric div {
        color: #0F172A;
        font-weight: 800;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## 🏙️ Dashboard Kota Serang")
    st.caption("Fiscal & Social Insight")

    st.divider()

    menu = st.radio(
        "Pilih halaman yang ingin dilihat:",
        [
            "🏠 Ringkasan Kota Serang",
            "💰 Pendapatan Fiskal",
            "🏗️ Belanja Pembangunan",
            "👥 Kondisi Sosial",
            "📊 Data & Statistik"
        ]
    )

    st.divider()

    st.markdown("### ⚙️ Filter Tahun")
    tahun_min = int(df_serang["Tahun"].min())
    tahun_max = int(df_serang["Tahun"].max())

    tahun_awal, tahun_akhir = st.slider(
        "Rentang tahun",
        min_value=tahun_min,
        max_value=tahun_max,
        value=(tahun_min, tahun_max)
    )

    st.divider()
    st.info("Dashboard ini menampilkan data khusus Kota Serang.")

df_filter = df_serang[
    (df_serang["Tahun"] >= tahun_awal) &
    (df_serang["Tahun"] <= tahun_akhir)
].sort_values("Tahun")

tahun_terakhir = df_filter["Tahun"].max()
data_terakhir = df_filter[df_filter["Tahun"] == tahun_terakhir].iloc[0]

# Header
st.markdown(f"""
<div style="
    background: linear-gradient(135deg, #2563EB, #7C3AED);
    padding: 30px;
    border-radius: 22px;
    color: white;
    margin-bottom: 25px;
">
    <h1 style="color:white; margin:0;">🏙️ Dashboard Kota Serang</h1>
    <p style="margin:8px 0 0 0; font-size:17px; opacity:0.9;">
        Analisis fiskal daerah, belanja pembangunan, dan kondisi sosial Kota Serang
    </p>
    <p style="margin:10px 0 0 0; font-size:14px; opacity:0.8;">
        Data tersedia: {tahun_min}–{tahun_max} | Filter aktif: {tahun_awal}–{tahun_akhir}
    </p>
</div>
""", unsafe_allow_html=True)

# ================= HALAMAN RINGKASAN =================
if menu == "🏠 Ringkasan Kota Serang":

    st.markdown("### 📌 Ringkasan Utama")

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    col1.metric("💰 PAD", f"{data_terakhir['PAD']:.2f}")
    col2.metric("🏛️ DAU", f"{data_terakhir['DAU_Grant']:.2f}")
    col3.metric("🏗️ DAK Fisik", f"{data_terakhir['DAK_Fisik']:.2f}")
    col4.metric("📉 Kemiskinan", f"{data_terakhir['KEMISKINAN']:.2f}%")
    col5.metric("👷 Pengangguran", f"{data_terakhir['PENGANGGURAN']:.2f}%")
    col6.metric("🎓 IPM", f"{data_terakhir['IPM']:.2f}")

    st.caption(f"Indikator di atas menunjukkan kondisi Kota Serang pada tahun {tahun_terakhir}.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 💰 Pendapatan Fiskal")

        fig, ax = plt.subplots(figsize=(8, 4))

        ax.plot(df_filter["Tahun"], df_filter["PAD"], marker="o", linewidth=2.5, color=BIRU, label="PAD")
        ax.plot(df_filter["Tahun"], df_filter["DAU_Grant"], marker="o", linewidth=2.5, color=HIJAU, label="DAU")
        ax.plot(df_filter["Tahun"], df_filter["DAK_Fisik"], marker="o", linewidth=2.5, color=KUNING, label="DAK Fisik")

        ax.set_title("Tren Pendapatan Fiskal", fontsize=13, fontweight="bold")
        ax.set_xlabel("Tahun")
        ax.set_ylabel("Nilai")
        ax.legend(frameon=False)
        ax.grid(True, linestyle="--", alpha=0.3)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        st.pyplot(fig, use_container_width=True)

    with col2:
        st.markdown("#### 👥 Kondisi Sosial")

        fig2, ax2 = plt.subplots(figsize=(8, 4))

        ax2.plot(df_filter["Tahun"], df_filter["KEMISKINAN"], marker="o", linewidth=2.5, color=MERAH, label="Kemiskinan (%)")
        ax2.plot(df_filter["Tahun"], df_filter["PENGANGGURAN"], marker="o", linewidth=2.5, color=KUNING, label="Pengangguran (%)")
        ax2.plot(df_filter["Tahun"], df_filter["IPM"], marker="o", linewidth=2.5, color=HIJAU, label="IPM")

        ax2.set_title("Tren Indikator Sosial", fontsize=13, fontweight="bold")
        ax2.set_xlabel("Tahun")
        ax2.set_ylabel("Nilai")
        ax2.legend(frameon=False)
        ax2.grid(True, linestyle="--", alpha=0.3)
        ax2.spines["top"].set_visible(False)
        ax2.spines["right"].set_visible(False)

        st.pyplot(fig2, use_container_width=True)

# ================= HALAMAN PENDAPATAN =================
elif menu == "💰 Pendapatan Fiskal":

    st.markdown("### 💰 Analisis Pendapatan Fiskal Daerah")

    fig, ax = plt.subplots(figsize=(12, 5))

    ax.plot(df_filter["Tahun"], df_filter["PAD"], marker="o", linewidth=2.5, color=BIRU, label="PAD")
    ax.plot(df_filter["Tahun"], df_filter["DAU_Grant"], marker="o", linewidth=2.5, color=HIJAU, label="DAU")
    ax.plot(df_filter["Tahun"], df_filter["DAK_Fisik"], marker="o", linewidth=2.5, color=KUNING, label="DAK Fisik")
    ax.plot(df_filter["Tahun"], df_filter["DAK_Nonfisik"], marker="o", linewidth=2.5, color=UNGU, label="DAK Nonfisik")
    ax.plot(df_filter["Tahun"], df_filter["DBH_PAJAK"], marker="o", linewidth=2.5, color=MERAH, label="DBH Pajak")

    ax.set_title("Tren Pendapatan Fiskal Kota Serang", fontsize=14, fontweight="bold")
    ax.set_xlabel("Tahun")
    ax.set_ylabel("Nilai")
    ax.legend(frameon=False)
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    st.pyplot(fig, use_container_width=True)

    st.markdown("#### 🏦 Komposisi Dana Transfer")

    kolom_transfer = [
        "DBH_PAJAK", "DBH_SDA", "DBH_Lainnya",
        "DAU_Grant", "DAU_Earmark",
        "DAK_Fisik", "DAK_Nonfisik"
    ]

    nilai_transfer = data_terakhir[kolom_transfer].astype(float)

    fig2, ax2 = plt.subplots(figsize=(11, 5))

    bars = ax2.bar(kolom_transfer, nilai_transfer, color=BIRU, alpha=0.85)

    ax2.set_title(f"Komposisi Dana Transfer Tahun {tahun_terakhir}", fontsize=14, fontweight="bold")
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

# ================= HALAMAN BELANJA =================
elif menu == "🏗️ Belanja Pembangunan":

    st.markdown("### 🏗️ Analisis Belanja Pembangunan")

    kolom_belanja = [
        "bm_pendidikan", "bm_kesehatan", "bm_perumahan",
        "bm_lingkungan", "bm_ekonomi", "bm_infrastruktur",
        "bm_pariwisata", "bm_perlindungan_sosial"
    ]

    pilihan_belanja = st.multiselect(
        "Pilih bidang belanja yang ingin ditampilkan:",
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

        warna_grafik = [BIRU, HIJAU, MERAH, KUNING, UNGU]

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
        st.warning("Pilih minimal satu bidang belanja.")

# ================= HALAMAN SOSIAL =================
elif menu == "👥 Kondisi Sosial":

    st.markdown("### 👥 Analisis Kondisi Sosial Kota Serang")

    col1, col2 = st.columns([2, 1])

    with col1:
        fig4, ax4 = plt.subplots(figsize=(10, 5))

        ax4.plot(df_filter["Tahun"], df_filter["KEMISKINAN"], marker="o", linewidth=2.5, color=MERAH, label="Kemiskinan (%)")
        ax4.plot(df_filter["Tahun"], df_filter["PENGANGGURAN"], marker="o", linewidth=2.5, color=KUNING, label="Pengangguran (%)")
        ax4.plot(df_filter["Tahun"], df_filter["KETIMPANGAN"], marker="o", linewidth=2.5, color=UNGU, label="Ketimpangan")

        ax4.set_title("Tren Indikator Sosial", fontsize=14, fontweight="bold")
        ax4.set_xlabel("Tahun")
        ax4.set_ylabel("Nilai")
        ax4.legend(frameon=False)
        ax4.grid(True, linestyle="--", alpha=0.3)
        ax4.spines["top"].set_visible(False)
        ax4.spines["right"].set_visible(False)

        st.pyplot(fig4, use_container_width=True)

    with col2:
        fig5, ax5 = plt.subplots(figsize=(6, 5))

        ax5.plot(df_filter["Tahun"], df_filter["IPM"], marker="o", linewidth=3, color=HIJAU)
        ax5.fill_between(df_filter["Tahun"], df_filter["IPM"], alpha=0.15, color=HIJAU)

        ax5.set_title("Perkembangan IPM", fontsize=14, fontweight="bold")
        ax5.set_xlabel("Tahun")
        ax5.set_ylabel("IPM")
        ax5.grid(True, linestyle="--", alpha=0.3)
        ax5.spines["top"].set_visible(False)
        ax5.spines["right"].set_visible(False)

        st.pyplot(fig5, use_container_width=True)

# ================= HALAMAN DATA =================
else:

    st.markdown("### 📊 Data dan Statistik Kota Serang")

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

    st.markdown("#### 🧮 Statistik Deskriptif")
    st.dataframe(pd.DataFrame(statistik), use_container_width=True, hide_index=True)

    st.markdown("#### 📋 Data Lengkap")
    st.dataframe(df_filter, use_container_width=True)

st.divider()
st.caption("Sumber data: dataset_fiskal_97_hipoFull.csv dari GitHub JUMRA-id/Dashboard-Kota-Serang. Dibuat menggunakan Streamlit, Pandas, NumPy, dan Matplotlib.")
