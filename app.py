# app.py
# Fiscal Insight Indonesia — Dashboard Analisis Fiskal dengan Streamlit
# Dataset sumber:
# https://raw.githubusercontent.com/Alam-A99/DATAAKSI/main/dataset_fiskal_97_hipoFull.csv

import re
import io
import urllib.error
import urllib.request

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

DATA_URL = "https://raw.githubusercontent.com/Alam-A99/DATAAKSI/main/dataset_fiskal_97_hipoFull.csv"

# ----------------------------- Konfigurasi halaman -----------------------------
st.set_page_config(
    page_title="Fiscal Insight Indonesia",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Tema biru tua dan kartu statistik
st.markdown(
    """
    <style>
    .stApp { background-color: #F4F7FB; }
    [data-testid="stSidebar"] { background: #102A43; }
    [data-testid="stSidebar"] * { color: #F0F4F8 !important; }
    .hero {
        padding: 1.35rem 1.6rem; border-radius: 18px; margin-bottom: 1rem;
        background: linear-gradient(120deg, #102A43 0%, #176B87 100%);
        color: white;
    }
    .hero h1 { margin: 0; color: white; font-size: 2rem; }
    .hero p { margin: .45rem 0 0 0; color: #D9EAF2; }
    .metric-card {
        background: white; border: 1px solid #E1E8F0; border-radius: 14px;
        padding: 1rem 1.1rem; min-height: 112px;
        box-shadow: 0 2px 8px rgba(16,42,67,.04);
    }
    .metric-label { color: #52606D; font-size: .82rem; margin-bottom: .45rem; }
    .metric-value { color: #102A43; font-size: 1.55rem; font-weight: 750; }
    .metric-note { color: #627D98; font-size: .75rem; margin-top: .35rem; }
    div[data-testid="stDataFrame"] { border-radius: 10px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------- Fungsi bantu -----------------------------
def norm_name(value):
    """Normalisasi nama kolom untuk pencocokan yang toleran."""
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def human_name(value):
    """Buat nama kolom lebih mudah dibaca."""
    return str(value).replace("_", " ").replace("-", " ").strip().title()


def is_year_column(series):
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return False
    return values.between(1800, 2200).mean() > 0.8 and values.nunique() > 1


@st.cache_data(show_spinner="Mengambil dataset dari GitHub...")
def load_data(url):
    """Membaca CSV dari URL dengan beberapa fallback separator/encoding."""
    errors = []
    for encoding in ("utf-8", "utf-8-sig", "latin1"):
        for sep in (",", ";", "\t", None):
            try:
                frame = pd.read_csv(url, encoding=encoding, sep=sep, engine="python")
                if frame.shape[1] > 1 and len(frame) > 0:
                    frame.columns = [str(c).strip() for c in frame.columns]
                    # Hilangkan kolom kosong atau kolom indeks tak sengaja
                    frame = frame.loc[:, ~frame.columns.astype(str).str.match(r"^Unnamed")]
                    return frame
            except Exception as exc:
                errors.append(str(exc))
    raise ValueError("CSV tidak dapat dibaca. Detail: " + (errors[-1] if errors else "format tidak dikenali"))


def convert_numeric_columns(frame):
    """Konversi kolom yang dominan numerik tanpa memaksa kolom teks menjadi angka."""
    out = frame.copy()
    for col in out.columns:
        if pd.api.types.is_numeric_dtype(out[col]):
            continue
        original = out[col]
        cleaned = (
            original.astype(str)
            .str.strip()
            .str.replace(r"(?<=\d)[.](?=\d{3}(?:\D|$))", "", regex=True)
            .str.replace(",", ".", regex=False)
            .str.replace("%", "", regex=False)
            .str.replace(r"[^\d.\-]", "", regex=True)
        )
        parsed = pd.to_numeric(cleaned, errors="coerce")
        nonempty = original.notna() & original.astype(str).str.strip().ne("")
        if nonempty.sum() and (parsed[nonempty].notna().mean() >= 0.85):
            out[col] = parsed
    return out


def find_column(columns, candidates):
    """Cari kolom berdasarkan nama yang mirip; hasil tetap berdasarkan kolom asli."""
    pairs = [(c, norm_name(c)) for c in columns]
    candidate_norms = [norm_name(x) for x in candidates]
    for target in candidate_norms:
        for col, normalized in pairs:
            if normalized == target:
                return col
    for target in candidate_norms:
        for col, normalized in pairs:
            if target and (target in normalized or normalized in target):
                return col
    return None


def format_number(value):
    if pd.isna(value) or not np.isfinite(value):
        return "—"
    value = float(value)
    abs_value = abs(value)
    if abs_value >= 1_000_000_000_000:
        return f"{value / 1_000_000_000_000:,.2f} T"
    if abs_value >= 1_000_000_000:
        return f"{value / 1_000_000_000:,.2f} M"
    if abs_value >= 1_000_000:
        return f"{value / 1_000_000:,.2f} jt"
    return f"{value:,.2f}"


def metric_card(label, value, note=""):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_matplotlib(fig):
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def safe_numeric_columns(frame):
    return [
        c for c in frame.columns
        if pd.api.types.is_numeric_dtype(frame[c])
        and frame[c].notna().sum() > 0
        and frame[c].nunique(dropna=True) > 1
    ]


def make_bar_chart(data, x, y, title, xlabel=None, ylabel=None, rotate=30):
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.bar(data[x].astype(str), data[y], color="#176B87")
    ax.set_title(title, loc="left", fontsize=13, fontweight="bold", color="#102A43")
    ax.set_xlabel(xlabel or human_name(x))
    ax.set_ylabel(ylabel or human_name(y))
    ax.tick_params(axis="x", rotation=rotate)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    return fig


def make_line_chart(data, x, y, title, group=None):
    fig, ax = plt.subplots(figsize=(10, 4.8))
    if group and group in data.columns:
        for label, part in data.groupby(group):
            part = part.sort_values(x)
            ax.plot(part[x], part[y], marker="o", linewidth=2, label=str(label))
        ax.legend(title=human_name(group), bbox_to_anchor=(1.02, 1), loc="upper left")
    else:
        part = data.sort_values(x)
        ax.plot(part[x], part[y], marker="o", linewidth=2.3, color="#176B87")
    ax.set_title(title, loc="left", fontsize=13, fontweight="bold", color="#102A43")
    ax.set_xlabel(human_name(x))
    ax.set_ylabel(human_name(y))
    ax.grid(alpha=0.25)
    fig.tight_layout()
    return fig


# ----------------------------- Memuat data -----------------------------
st.markdown(
    """
    <div class="hero">
        <h1>📊 Fiscal Insight Indonesia</h1>
        <p>Dashboard interaktif untuk mengeksplorasi indikator fiskal, belanja sektor, dan kondisi sosial-ekonomi daerah.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("## FISCAL INSIGHT")
    st.caption("Analisis data fiskal daerah")
    menu = st.radio(
        "Pilih menu",
        [
            "1. Overview",
            "2. Analisis Fiskal",
            "3. Analisis Belanja",
            "4. Sosial-Ekonomi",
            "5. Perbandingan Kota",
            "6. Korelasi Data",
            "7. Data & Unduh",
        ],
    )
    st.divider()
    st.caption("Sumber data")
    st.markdown("[Dataset CSV di GitHub](https://github.com/Alam-A99/DATAAKSI/blob/main/dataset_fiskal_97_hipoFull.csv)")
    if st.button("Muat ulang dataset", use_container_width=True):
        load_data.clear()
        st.rerun()

try:
    raw_df = load_data(DATA_URL)
except Exception as error:
    st.error("Dataset gagal dimuat dari GitHub.")
    st.exception(error)
    st.info("Periksa koneksi internet atau unduh CSV dari GitHub, lalu unggah menggunakan opsi di bawah.")
    uploaded = st.file_uploader("Unggah file CSV dataset", type=["csv"])
    if uploaded is None:
        st.stop()
    try:
        raw_df = pd.read_csv(uploaded, sep=None, engine="python")
    except Exception as upload_error:
        st.error(f"File CSV gagal dibaca: {upload_error}")
        st.stop()

if raw_df.empty:
    st.error("Dataset kosong. Dashboard dihentikan agar tidak menghasilkan ringkasan yang menyesatkan.")
    st.stop()

# Tampilkan kondisi asli dan data hasil konversi
df = convert_numeric_columns(raw_df)
all_columns = list(df.columns)
numeric_columns = safe_numeric_columns(df)

city_col = find_column(all_columns, ["Kota", "Kabupaten/Kota", "Nama Kota", "Wilayah", "Daerah", "City"])
year_col = find_column(all_columns, ["Tahun", "Year", "Periode"])
if year_col is None:
    for col in all_columns:
        if is_year_column(df[col]):
            year_col = col
            df[col] = pd.to_numeric(df[col], errors="coerce")
            break
if year_col and year_col not in numeric_columns:
    df[year_col] = pd.to_numeric(df[year_col], errors="coerce")
    numeric_columns = safe_numeric_columns(df)

# Kandidat kolom fiskal dan sektor; hanya dipakai jika kolom cocok ditemukan.
fiscal_candidates = {
    "PAD": ["PAD", "Pendapatan Asli Daerah"],
    "DBH Pajak": ["DBH_PAJAK", "DBH Pajak", "Dana Bagi Hasil Pajak"],
    "DAU": ["DAU_Grant", "DAU", "Dana Alokasi Umum"],
    "DAK Fisik": ["DAK_Fisik", "DAK Fisik"],
    "DAK Nonfisik": ["DAK_Nonfisik", "DAK Nonfisik"],
}
sector_candidates = {
    "Pendidikan": ["Belanja_Pendidikan", "Pendidikan", "Education", "Alokasi_Pendidikan"],
    "Kesehatan": ["Belanja_Kesehatan", "Kesehatan", "Health", "Alokasi_Kesehatan"],
    "Infrastruktur": ["Belanja_Infrastruktur", "Infrastruktur", "Infrastructure"],
    "Ekonomi": ["Belanja_Ekonomi", "Ekonomi", "Economic"],
}
social_candidates = {
    "Kemiskinan": ["KEMISKINAN", "Kemiskinan", "Poverty"],
    "Pengangguran": ["PENGANGGURAN", "Pengangguran", "Unemployment", "TPT"],
    "Ketimpangan": ["KETIMPANGAN", "Ketimpangan", "Gini", "Gini Ratio"],
    "IPM": ["IPM", "Indeks Pembangunan Manusia", "HDI"],
}
fiscal_cols = {label: find_column(all_columns, candidates) for label, candidates in fiscal_candidates.items()}
sector_cols = {label: find_column(all_columns, candidates) for label, candidates in sector_candidates.items()}
social_cols = {label: find_column(all_columns, candidates) for label, candidates in social_candidates.items()}

# Sidebar filter global
with st.sidebar:
    st.markdown("### Filter data")
    filtered = df.copy()
    if year_col and df[year_col].notna().any():
        years = sorted(df[year_col].dropna().unique().tolist())
        if years:
            year_range = st.select_slider(
                "Rentang tahun",
                options=years,
                value=(years[0], years[-1]),
                format_func=lambda x: str(int(x)) if float(x).is_integer() else str(x),
            )
            filtered = filtered[filtered[year_col].between(year_range[0], year_range[1])]
    else:
        st.caption("Kolom tahun tidak terdeteksi; filter tahun tidak tersedia.")

    if city_col:
        # Dashboard ini sengaja dibatasi hanya untuk Kota Serang.
        city_values = sorted(df[city_col].dropna().astype(str).unique().tolist())
        serang_mask = df[city_col].astype(str).str.contains(r"serang", case=False, na=False)
        serang_values = sorted(df.loc[serang_mask, city_col].dropna().astype(str).unique().tolist())
        st.text_input("Kota yang dianalisis", value="Kota Serang", disabled=True)
        if serang_values:
            filtered = filtered[filtered[city_col].astype(str).isin(serang_values)]
            st.caption("Seluruh analisis dibatasi pada: " + ", ".join(serang_values))
        else:
            st.error("Kota Serang tidak ditemukan pada kolom wilayah dataset. Nilai wilayah yang tersedia: " + ", ".join(city_values[:30]))
            st.stop()
    else:
        st.error("Kolom kota/wilayah tidak terdeteksi. Periksa nama kolom pada dataset sebelum analisis.")
        st.stop()

    st.caption(f"Baris setelah filter: {len(filtered):,}")

if filtered.empty:
    st.warning("Tidak ada baris yang cocok dengan filter. Pilih kembali tahun atau kota pada sidebar.")
    st.stop()

# Ringkasan umum untuk bagian yang memakai filter
city_count = filtered[city_col].nunique(dropna=True) if city_col else None
year_min = filtered[year_col].min() if year_col and filtered[year_col].notna().any() else None
year_max = filtered[year_col].max() if year_col and filtered[year_col].notna().any() else None

# ----------------------------- 1. Overview -----------------------------
if menu == "1. Overview":
    st.subheader("Ringkasan Dataset")
    st.caption("Semua angka dihitung dari data yang lolos filter di sidebar.")
    cols = st.columns(4)
    with cols[0]:
        metric_card("Jumlah baris", f"{len(filtered):,}", "Observasi setelah filter")
    with cols[1]:
        metric_card("Jumlah kolom", f"{filtered.shape[1]:,}", "Variabel pada dataset")
    with cols[2]:
        metric_card("Kota/wilayah unik", f"{city_count:,}" if city_count is not None else "Tidak tersedia", "Berdasarkan kolom wilayah" if city_col else "Kolom wilayah tidak terdeteksi")
    with cols[3]:
        period = f"{int(year_min)}–{int(year_max)}" if year_min is not None and year_max is not None else "Tidak tersedia"
        metric_card("Rentang tahun", period, "Berdasarkan kolom tahun" if year_col else "Kolom tahun tidak terdeteksi")

    st.markdown("### Pratinjau data")
    st.dataframe(filtered.head(15), use_container_width=True, hide_index=True)

    left, right = st.columns(2)
    with left:
        st.markdown("### Kelengkapan data")
        missing = filtered.isna().sum().sort_values(ascending=False).head(12)
        missing = missing[missing > 0]
        if not missing.empty:
            fig, ax = plt.subplots(figsize=(7, 4))
            ax.barh(missing.index[::-1], missing.values[::-1], color="#176B87")
            ax.set_title("Jumlah nilai kosong per kolom", loc="left", color="#102A43", fontweight="bold")
            ax.set_xlabel("Jumlah nilai kosong")
            ax.grid(axis="x", alpha=.25)
            fig.tight_layout()
            show_matplotlib(fig)
        else:
            st.success("Tidak ditemukan nilai kosong pada data yang sedang difilter.")

    with right:
        st.markdown("### Variabel numerik")
        if numeric_columns:
            selected_num = st.selectbox("Pilih variabel", numeric_columns, key="overview_numeric")
            vals = filtered[selected_num].dropna()
            if not vals.empty:
                fig, ax = plt.subplots(figsize=(7, 4))
                ax.hist(vals, bins=min(25, max(5, int(np.sqrt(len(vals))))), color="#176B87", edgecolor="white")
                ax.set_title(f"Distribusi {human_name(selected_num)}", loc="left", color="#102A43", fontweight="bold")
                ax.set_xlabel(human_name(selected_num))
                ax.set_ylabel("Frekuensi")
                ax.grid(axis="y", alpha=.2)
                fig.tight_layout()
                show_matplotlib(fig)
        else:
            st.info("Tidak ada kolom numerik yang dapat dianalisis setelah validasi.")

    st.markdown("### Statistik deskriptif")
    if numeric_columns:
        st.dataframe(filtered[numeric_columns].describe().T, use_container_width=True)
    else:
        st.info("Statistik deskriptif tidak tersedia karena kolom numerik belum terdeteksi.")

# ----------------------------- 2. Analisis Fiskal -----------------------------
elif menu == "2. Analisis Fiskal":
    st.subheader("Analisis Indikator Fiskal")
    available = {label: col for label, col in fiscal_cols.items() if col and col in numeric_columns}
    if not available:
        st.warning("Kolom fiskal yang dikenali otomatis tidak tersedia atau bukan numerik. Gunakan pilihan kolom numerik di bawah.")
        if not numeric_columns:
            st.stop()
        selected_fiscal = st.multiselect("Pilih kolom fiskal yang ingin dianalisis", numeric_columns, default=numeric_columns[:min(4, len(numeric_columns))])
        available = {human_name(c): c for c in selected_fiscal}
    else:
        st.caption("Kolom berikut dikenali dari nama dataset: " + ", ".join(f"{k} ({v})" for k, v in available.items()))

    selected_label = st.selectbox("Indikator fiskal", list(available.keys()))
    selected_col = available[selected_label]
    vals = filtered[selected_col].dropna()
    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card("Rata-rata", format_number(vals.mean()) if len(vals) else "—", selected_label)
    with c2:
        metric_card("Median", format_number(vals.median()) if len(vals) else "—", selected_label)
    with c3:
        metric_card("Total", format_number(vals.sum()) if len(vals) else "—", "Penjumlahan nilai non-kosong")

    if city_col:
        agg = filtered.groupby(city_col, dropna=True)[selected_col].mean().dropna().sort_values(ascending=False).head(15).reset_index()
        if not agg.empty:
            st.markdown("### Rata-rata indikator per kota/wilayah")
            show_matplotlib(make_bar_chart(agg, city_col, selected_col, f"15 wilayah dengan rata-rata {selected_label} tertinggi", rotate=45))
    if year_col:
        trend = filtered.groupby(year_col, dropna=True)[selected_col].mean().dropna().reset_index().sort_values(year_col)
        if not trend.empty:
            st.markdown("### Perkembangan dari tahun ke tahun")
            show_matplotlib(make_line_chart(trend, year_col, selected_col, f"Tren rata-rata {selected_label}"))
            if len(trend) >= 2:
                first, last = trend.iloc[0][selected_col], trend.iloc[-1][selected_col]
                if pd.notna(first) and first != 0:
                    pct = ((last - first) / abs(first)) * 100
                    st.info(f"Perubahan antara titik tahun pertama dan terakhir pada data terfilter: {pct:,.2f}%. Ini perbandingan dua titik, bukan bukti penyebab perubahan.")
    st.markdown("### Tabel ringkasan")
    st.dataframe(filtered[[c for c in [city_col, year_col, selected_col] if c]].sort_values(year_col) if year_col else filtered[[c for c in [city_col, selected_col] if c]], use_container_width=True, hide_index=True)

# ----------------------------- 3. Analisis Belanja -----------------------------
elif menu == "3. Analisis Belanja":
    st.subheader("Analisis Alokasi Belanja Sektor")
    available = {label: col for label, col in sector_cols.items() if col and col in numeric_columns}
    if not available:
        st.warning("Kolom belanja sektor tidak terdeteksi otomatis. Pilih kolom yang sesuai dari daftar numerik.")
        if not numeric_columns:
            st.stop()
        chosen = st.multiselect("Pilih kolom belanja/sektor", numeric_columns, default=numeric_columns[:min(5, len(numeric_columns))])
        available = {human_name(c): c for c in chosen}
    else:
        st.caption("Kolom sektor yang dikenali: " + ", ".join(f"{k} ({v})" for k, v in available.items()))

    if not available:
        st.info("Pilih minimal satu kolom numerik untuk melanjutkan.")
        st.stop()

    selected_sectors = st.multiselect("Sektor yang ditampilkan", list(available.keys()), default=list(available.keys()))
    sector_map = {k: available[k] for k in selected_sectors}
    if sector_map:
        totals = pd.Series({label: filtered[col].sum(skipna=True) for label, col in sector_map.items()}).sort_values(ascending=False)
        fig, ax = plt.subplots(figsize=(9, 4.8))
        ax.bar(totals.index, totals.values, color="#176B87")
        ax.set_title("Total nilai kolom sektor pada data terfilter", loc="left", color="#102A43", fontweight="bold")
        ax.set_ylabel("Total")
        ax.tick_params(axis="x", rotation=25)
        ax.grid(axis="y", alpha=.25)
        fig.tight_layout()
        show_matplotlib(fig)

        if year_col:
            st.markdown("### Tren sektor per tahun")
            trend_data = filtered.groupby(year_col)[list(sector_map.values())].mean(numeric_only=True).reset_index().sort_values(year_col)
            fig, ax = plt.subplots(figsize=(10, 5))
            for label, col in sector_map.items():
                ax.plot(trend_data[year_col], trend_data[col], marker="o", label=label)
            ax.set_title("Rata-rata indikator sektor per tahun", loc="left", color="#102A43", fontweight="bold")
            ax.set_xlabel(human_name(year_col))
            ax.set_ylabel("Rata-rata")
            ax.grid(alpha=.25)
            ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left")
            fig.tight_layout()
            show_matplotlib(fig)
        st.markdown("### Ringkasan per sektor")
        summary = pd.DataFrame({
            "Sektor": list(sector_map.keys()),
            "Kolom dataset": list(sector_map.values()),
            "Total": [filtered[c].sum(skipna=True) for c in sector_map.values()],
            "Rata-rata": [filtered[c].mean() for c in sector_map.values()],
            "Median": [filtered[c].median() for c in sector_map.values()],
            "Nilai kosong": [filtered[c].isna().sum() for c in sector_map.values()],
        })
        st.dataframe(summary, use_container_width=True, hide_index=True)
        st.caption("Pastikan satuan dan definisi setiap kolom sebanding sebelum menafsirkan perbandingan antar sektor.")

# ----------------------------- 4. Sosial-Ekonomi -----------------------------
elif menu == "4. Sosial-Ekonomi":
    st.subheader("Analisis Indikator Sosial-Ekonomi")
    available = {label: col for label, col in social_cols.items() if col and col in numeric_columns}
    if not available:
        st.warning("Kolom sosial-ekonomi belum dikenali otomatis. Pilih kolom yang sesuai.")
        if not numeric_columns:
            st.stop()
        chosen = st.multiselect("Pilih indikator sosial-ekonomi", numeric_columns, default=numeric_columns[:min(4, len(numeric_columns))])
        available = {human_name(c): c for c in chosen}
    else:
        st.caption("Kolom yang dikenali: " + ", ".join(f"{k} ({v})" for k, v in available.items()))

    if not available:
        st.info("Pilih minimal satu indikator numerik.")
        st.stop()

    selected_label = st.selectbox("Pilih indikator", list(available.keys()))
    selected_col = available[selected_label]
    vals = filtered[selected_col].dropna()
    a, b, c = st.columns(3)
    with a:
        metric_card("Rata-rata", format_number(vals.mean()) if len(vals) else "—", selected_label)
    with b:
        metric_card("Minimum", format_number(vals.min()) if len(vals) else "—", selected_label)
    with c:
        metric_card("Maksimum", format_number(vals.max()) if len(vals) else "—", selected_label)

    if year_col:
        trend = filtered.groupby(year_col)[selected_col].mean().dropna().reset_index().sort_values(year_col)
        if not trend.empty:
            show_matplotlib(make_line_chart(trend, year_col, selected_col, f"Tren {selected_label}"))
    if city_col:
        city_avg = filtered.groupby(city_col)[selected_col].mean().dropna().sort_values(ascending=False).reset_index()
        if not city_avg.empty:
            st.markdown("### Perbandingan antarwilayah")
            show_matplotlib(make_bar_chart(city_avg.head(15), city_col, selected_col, f"15 wilayah dengan rata-rata {selected_label} tertinggi", rotate=45))
    st.markdown("### Statistik deskriptif")
    st.dataframe(filtered[[selected_col]].describe().T, use_container_width=True)

# ----------------------------- 5. Perbandingan Kota -----------------------------
elif menu == "5. Perbandingan Kota":
    st.subheader("Perbandingan Kota/Wilayah")
    if not city_col:
        st.warning("Kolom kota/wilayah tidak ditemukan. Periksa nama kolom pada menu Data & Unduh.")
        st.stop()
    if not numeric_columns:
        st.warning("Tidak ada variabel numerik yang bisa dibandingkan.")
        st.stop()

    indicator = st.selectbox("Indikator perbandingan", numeric_columns, key="city_indicator")
    ranking = st.radio("Urutkan berdasarkan", ["Tertinggi", "Terendah"], horizontal=True)
    city_summary = filtered.groupby(city_col)[indicator].agg(["mean", "median", "count"]).dropna()
    city_summary = city_summary.sort_values("mean", ascending=(ranking == "Terendah")).reset_index()
    city_summary.columns = [city_col, "Rata-rata", "Median", "Jumlah observasi"]
    top_n = st.slider("Jumlah wilayah yang ditampilkan", min_value=5, max_value=max(5, min(30, len(city_summary))) if len(city_summary) >= 5 else 5, value=min(10, max(5, len(city_summary))))
    view = city_summary.head(top_n)
    if not view.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.barh(view[city_col].astype(str)[::-1], view["Rata-rata"][::-1], color="#176B87")
        ax.set_title(f"Perbandingan wilayah berdasarkan {human_name(indicator)}", loc="left", color="#102A43", fontweight="bold")
        ax.set_xlabel("Rata-rata")
        ax.grid(axis="x", alpha=.25)
        fig.tight_layout()
        show_matplotlib(fig)
    st.dataframe(city_summary, use_container_width=True, hide_index=True)
    st.download_button("Unduh tabel perbandingan CSV", city_summary.to_csv(index=False).encode("utf-8-sig"), "perbandingan_wilayah.csv", "text/csv")

# ----------------------------- 6. Korelasi Data -----------------------------
elif menu == "6. Korelasi Data":
    st.subheader("Analisis Korelasi")
    st.caption("Korelasi mengukur keterkaitan linear antarvariabel; tidak membuktikan sebab-akibat.")
    corr_candidates = [c for c in numeric_columns if c != year_col]
    if len(corr_candidates) < 2:
        st.warning("Diperlukan minimal dua kolom numerik dengan variasi nilai.")
        st.stop()

    chosen = st.multiselect(
        "Pilih variabel untuk matriks korelasi",
        corr_candidates,
        default=corr_candidates[:min(10, len(corr_candidates))],
    )
    method = st.selectbox("Metode korelasi", ["pearson", "spearman"], help="Pearson untuk hubungan linear; Spearman untuk hubungan monotonik berbasis peringkat.")
    if len(chosen) >= 2:
        corr = filtered[chosen].corr(method=method, min_periods=3)
        fig, ax = plt.subplots(figsize=(max(7, len(chosen) * .8), max(5, len(chosen) * .65)))
        image = ax.imshow(corr.values, vmin=-1, vmax=1, cmap="RdBu_r", aspect="auto")
        ax.set_xticks(range(len(chosen)))
        ax.set_yticks(range(len(chosen)))
        ax.set_xticklabels([human_name(c) for c in chosen], rotation=45, ha="right")
        ax.set_yticklabels([human_name(c) for c in chosen])
        for i in range(len(chosen)):
            for j in range(len(chosen)):
                val = corr.iloc[i, j]
                label = f"{val:.2f}" if pd.notna(val) else "NA"
                ax.text(j, i, label, ha="center", va="center", fontsize=8, color="black")
        ax.set_title(f"Matriks Korelasi ({method.title()})", loc="left", color="#102A43", fontweight="bold")
        fig.colorbar(image, ax=ax, shrink=.8, label="Koefisien korelasi")
        fig.tight_layout()
        show_matplotlib(fig)
        st.dataframe(corr.style.format("{:.3f}", na_rep="—"), use_container_width=True)

        st.markdown("### Pasangan korelasi paling kuat")
        pairs = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool)).stack().reset_index()
        if not pairs.empty:
            pairs.columns = ["Variabel 1", "Variabel 2", "Korelasi"]
            pairs["Kekuatan absolut"] = pairs["Korelasi"].abs()
            pairs = pairs.sort_values("Kekuatan absolut", ascending=False)
            st.dataframe(pairs.drop(columns="Kekuatan absolut").head(10), use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada pasangan variabel yang cukup untuk dihitung.")
    else:
        st.info("Pilih minimal dua variabel untuk membuat matriks korelasi.")

# ----------------------------- 7. Data & Unduh -----------------------------
elif menu == "7. Data & Unduh":
    st.subheader("Data, Validasi, dan Unduh")
    st.markdown("### Pemeriksaan kualitas data")
    quality = pd.DataFrame({
        "Kolom": df.columns,
        "Tipe data setelah konversi": [str(df[c].dtype) for c in df.columns],
        "Nilai kosong": [int(df[c].isna().sum()) for c in df.columns],
        "Persentase kosong (%)": [round(float(df[c].isna().mean() * 100), 2) for c in df.columns],
        "Nilai unik": [int(df[c].nunique(dropna=True)) for c in df.columns],
    })
    st.dataframe(quality, use_container_width=True, hide_index=True)

    d1, d2, d3 = st.columns(3)
    with d1:
        metric_card("Baris data asli", f"{len(raw_df):,}", "Sebelum filter")
    with d2:
        metric_card("Duplikat seluruh baris", f"{int(df.duplicated().sum()):,}", "Baris identik")
    with d3:
        metric_card("Kolom numerik", f"{len(numeric_columns):,}", "Setelah konversi konservatif")

    st.markdown("### Tabel data terfilter")
    search = st.text_input("Cari teks pada data (opsional)", placeholder="Contoh: nama kota atau wilayah")
    data_view = filtered.copy()
    if search.strip():
        mask = data_view.astype(str).apply(lambda col: col.str.contains(search.strip(), case=False, na=False)).any(axis=1)
        data_view = data_view[mask]
    st.write(f"Menampilkan {len(data_view):,} baris.")
    st.dataframe(data_view, use_container_width=True, hide_index=True)

    csv_bytes = data_view.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "⬇️ Unduh data terfilter (CSV)",
        data=csv_bytes,
        file_name="fiscal_insight_data_terfilter.csv",
        mime="text/csv",
        use_container_width=True,
    )
    st.download_button(
        "⬇️ Unduh laporan kualitas data (CSV)",
        data=quality.to_csv(index=False).encode("utf-8-sig"),
        file_name="laporan_kualitas_data.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.markdown("### Nama kolom yang tersedia")
    st.code("\n".join(str(c) for c in df.columns), language="text")

st.divider()
st.caption(
    "Fiscal Insight Indonesia • Data ditampilkan sesuai dataset sumber dan filter yang dipilih. "
    "Kolom yang tidak terdeteksi tidak dibuat-buat; gunakan menu Data & Unduh untuk memeriksa nama kolom asli."
)
