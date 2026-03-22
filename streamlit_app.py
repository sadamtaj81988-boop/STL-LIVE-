import streamlit as st
import pandas as pd
import time

st.set_page_config(
    page_title="STL LIVE — Structured Intelligence Engine",
    layout="wide"
)

# -----------------------------
# STYLE
# -----------------------------
st.markdown(
    """
    <style>
    .main {background-color: #0b1020; color: white;}
    .stApp {background-color: #0b1020; color: white;}
    h1, h2, h3, h4, h5, h6, p, div, label, span {
        color: white !important;
    }
    .metric-card {
        padding: 16px;
        border-radius: 14px;
        background: #12182b;
        border: 1px solid #222a44;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# STL ENGINE HELPERS
# -----------------------------
def detect_fragments(df: pd.DataFrame):
    issues = []

    required_cols = ["channel", "visitors", "purchases", "revenue"]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        issues.append(f"Missing required columns: {', '.join(missing_cols)}")
        return issues

    if df["visitors"].isna().any():
        issues.append("Some visitor values are missing.")
    if df["purchases"].isna().any():
        issues.append("Some purchase values are missing.")
    if df["revenue"].isna().any():
        issues.append("Some revenue values are missing.")
    if (df["visitors"] <= 0).any():
        issues.append("Some visitor values are zero or negative.")
    if (df["purchases"] < 0).any():
        issues.append("Some purchase values are negative.")
    if (df["revenue"] < 0).any():
        issues.append("Some revenue values are negative.")
    if (df["purchases"] > df["visitors"]).any():
        issues.append("Some purchases exceed visitors.")
    if df["channel"].duplicated().any():
        issues.append("Duplicate channel rows detected.")

    return issues


def process_data(df: pd.DataFrame):
    clean = df.copy()
    clean["channel"] = clean["channel"].astype(str).str.strip()
    clean["visitors"] = pd.to_numeric(clean["visitors"], errors="coerce")
    clean["purchases"] = pd.to_numeric(clean["purchases"], errors="coerce")
    clean["revenue"] = pd.to_numeric(clean["revenue"], errors="coerce")
    clean = clean.dropna(subset=["channel", "visitors", "purchases", "revenue"])
    clean = clean[clean["visitors"] > 0]
    clean = clean[clean["purchases"] >= 0]
    clean = clean[clean["revenue"] >= 0]
    clean = clean[clean["purchases"] <= clean["visitors"]]
    clean = clean.drop_duplicates(subset=["channel"], keep="first")
    clean["conversion"] = clean["purchases"] / clean["visitors"]
    clean["aov"] = clean["revenue"] / clean["purchases"].replace(0, pd.NA)
    clean["aov"] = clean["aov"].fillna(0)
    return clean.reset_index(drop=True)


def validate_data(df: pd.DataFrame):
    if df.empty:
        return False
    return all(col in df.columns for col in ["channel", "visitors", "purchases", "revenue", "conversion", "aov"])


def hydro_score(raw_df: pd.DataFrame, clean_df: pd.DataFrame):
    if len(raw_df) == 0:
        return 0.0

    completeness = 100.0 * (1 - raw_df[["channel", "visitors", "purchases", "revenue"]].isna().sum().sum() / max(1, raw_df[["channel", "visitors", "purchases", "revenue"]].size))
    validity = 100.0 * (len(clean_df) / max(1, len(raw_df)))
    consistency = 100.0
    if "purchases" in raw_df.columns and "visitors" in raw_df.columns:
        bad = ((pd.to_numeric(raw_df["purchases"], errors="coerce") > pd.to_numeric(raw_df["visitors"], errors="coerce"))).fillna(False).sum()
        consistency = 100.0 * (1 - bad / max(1, len(raw_df)))

    integrity = 100.0
    if "channel" in raw_df.columns:
        dup = raw_df["channel"].astype(str).duplicated().sum()
        integrity = 100.0 * (1 - dup / max(1, len(raw_df)))

    reliability = (completeness + validity + consistency + integrity) / 4
    return round(max(0.0, min(100.0, reliability)), 2)


def classify_hydro(score: float):
    if score >= 90:
        return "HALAAL / STRONG"
    if score >= 70:
        return "STABLE"
    if score >= 50:
        return "RISK"
    return "HARAM / BROKEN"


def run_stl_engine(df: pd.DataFrame):
    fragments = detect_fragments(df)
    clean = process_data(df) if all(c in df.columns for c in ["channel", "visitors", "purchases", "revenue"]) else pd.DataFrame()
    valid = validate_data(clean)

    if valid:
        total_revenue = float(clean["revenue"].sum())
        total_visitors = float(clean["visitors"].sum())
        total_purchases = float(clean["purchases"].sum())
        conversion_rate = (total_purchases / total_visitors) if total_visitors > 0 else 0.0
        weakest_channel = clean.loc[clean["conversion"].idxmin(), "channel"] if not clean.empty else "N/A"
        hydro = hydro_score(df, clean)
        label = classify_hydro(hydro)
    else:
        total_revenue = 0.0
        total_visitors = 0.0
        total_purchases = 0.0
        conversion_rate = 0.0
        weakest_channel = "N/A"
        hydro = hydro_score(df, clean) if not clean.empty else 0.0
        label = classify_hydro(hydro)

    return {
        "fragments": fragments,
        "clean_data": clean,
        "valid": valid,
        "total_revenue": total_revenue,
        "total_visitors": total_visitors,
        "total_purchases": total_purchases,
        "conversion_rate": conversion_rate,
        "weakest_channel": weakest_channel,
        "hydro_score": hydro,
        "hydro_label": label,
    }


def load_demo_data():
    return pd.DataFrame(
        {
            "channel": ["Store", "Online", "Marketplace"],
            "visitors": [2000, 10000, 3000],
            "purchases": [400, 200, 90],
            "revenue": [12000, 8000, 4500],
        }
    )

# -----------------------------
# SIDEBAR / CONTROL LAYER
# -----------------------------
st.sidebar.title("STL Navigation")

page = st.sidebar.selectbox(
    "Section",
    ["Dashboard", "Blueprint", "Tracking", "Control Layer"]
)

st.sidebar.subheader("Live Controls")

input_mode = st.sidebar.radio(
    "Input Mode",
    ["Manual", "Demo Data", "Upload CSV"]
)

auto_refresh = st.sidebar.checkbox("Auto Refresh", value=False)
refresh_rate = st.sidebar.slider("Refresh every (sec)", 5, 60, 10)

if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()

# -----------------------------
# INPUT MODES
# -----------------------------
df = None

if input_mode == "Manual":
    st.sidebar.markdown("---")
    st.sidebar.subheader("Manual Inputs")

    store_visitors = st.sidebar.number_input("Store Visitors", min_value=0, value=2000)
    online_visitors = st.sidebar.number_input("Online Visitors", min_value=0, value=10000)
    marketplace_visitors = st.sidebar.number_input("Marketplace Visitors", min_value=0, value=3000)

    store_purchases = st.sidebar.number_input("Store Purchases", min_value=0, value=400)
    online_purchases = st.sidebar.number_input("Online Purchases", min_value=0, value=200)
    marketplace_purchases = st.sidebar.number_input("Marketplace Purchases", min_value=0, value=90)

    store_revenue = st.sidebar.number_input("Store Revenue", min_value=0, value=12000)
    online_revenue = st.sidebar.number_input("Online Revenue", min_value=0, value=8000)
    marketplace_revenue = st.sidebar.number_input("Marketplace Revenue", min_value=0, value=4500)

    df = pd.DataFrame(
        {
            "channel": ["Store", "Online", "Marketplace"],
            "visitors": [store_visitors, online_visitors, marketplace_visitors],
            "purchases": [store_purchases, online_purchases, marketplace_purchases],
            "revenue": [store_revenue, online_revenue, marketplace_revenue],
        }
    )

elif input_mode == "Demo Data":
    df = load_demo_data()

elif input_mode == "Upload CSV":
    uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)

# -----------------------------
# RUN ENGINE
# -----------------------------
result = None
if df is not None:
    result = run_stl_engine(df)

# -----------------------------
# PAGE: DASHBOARD
# -----------------------------
if page == "Dashboard":
    st.title("STL LIVE — Structured Intelligence Engine")
    st.caption("Real-time business diagnostics and decision system")

    if df is None:
        st.info("Choose Manual, Demo Data, or Upload CSV from the sidebar.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("STL LIVE", f'{result["hydro_score"] / 100:.2f}')
        c2.metric("Hydro Score", f'{result["hydro_score"]}%')
        c3.metric("Total Revenue", f'${result["total_revenue"]:,.0f}')
        c4.metric("Conversion %", f'{result["conversion_rate"] * 100:.2f}%')

        st.write(f'**Weakest Channel:** {result["weakest_channel"]}')
        st.write(f'**System Status:** {result["hydro_label"]}')

        if result["conversion_rate"] < 0.05:
            st.error("🚨 Low conversion detected")
        if result["fragments"]:
            st.warning("⚠️ Fragments detected in input data")

        st.subheader("Channel Performance")
        st.dataframe(result["clean_data"], use_container_width=True)

        if not result["clean_data"].empty:
            st.bar_chart(result["clean_data"].set_index("channel")["revenue"])
            st.line_chart(result["clean_data"].set_index("channel")["conversion"])

        st.subheader("Raw Input")
        st.dataframe(df, use_container_width=True)

# -----------------------------
# PAGE: BLUEPRINT
# -----------------------------
elif page == "Blueprint":
    st.title("STL Blueprint")
    st.markdown(
        """
        **STL Flow**

        - **WEST** → Input / Understood
        - **SOUTH** → Observation / Filtering
        - **CENTER** → Process / Logic / Time
        - **NORTH** → Validation / Storage
        - **EAST** → Output / Hydro / Credit

        **Engine Formula**

        `STL Intelligence = ((Input × Observation × Processing × Validation × Output × Governance)) ÷ Fragmentation`

        **Pipeline**

        `Raw Data → Ingestion → Processing → Validation → Storage → Output → Hydro`
        """
    )

# -----------------------------
# PAGE: TRACKING
# -----------------------------
elif page == "Tracking":
    st.title("Tracking")

    if df is None:
        st.info("No data loaded yet.")
    else:
        st.subheader("Input Snapshot")
        st.dataframe(df, use_container_width=True)

        st.subheader("Fragment Log")
        if result["fragments"]:
            for issue in result["fragments"]:
                st.write(f"- {issue}")
        else:
            st.success("No fragments detected.")

        st.subheader("Validation Status")
        st.write(f"Valid: {result['valid']}")
        st.write(f"Hydro: {result['hydro_score']}%")
        st.write(f"Classification: {result['hydro_label']}")

# -----------------------------
# PAGE: CONTROL LAYER
# -----------------------------
elif page == "Control Layer":
    st.title("Control Layer")
    st.write(f"Input Mode: {input_mode}")
    st.write(f"Auto Refresh: {auto_refresh}")
    st.write(f"Refresh Rate: {refresh_rate} sec")
    st.write("This layer controls navigation, input selection, and system refresh behavior.")

# =========================
# HYDRO SCORE (INTELLIGENCE)
# =========================

st.subheader("💧 STL Hydro Score")

def hydro_score(df):
    # Conversion rates
    df["conversion"] = df["purchases"] / df["visitors"]

    # Revenue efficiency
    df["efficiency"] = df["revenue"] / df["purchases"]

    # Normalize scores
    conv_score = df["conversion"].mean()
    eff_score = df["efficiency"].mean()

    score = (conv_score * 0.6) + (eff_score * 0.4)

    return round(score, 2)

score = hydro_score(df)

st.metric("Hydro Score", score)

# Alerts
st.subheader("🚨 STL Alerts")

for i, row in df.iterrows():
    if row["purchases"] / row["visitors"] < 0.1:
        st.warning(f"Low conversion detected in {row['channel']}")

    if row["revenue"] / row["purchases"] < 20:
        st.warning(f"Low revenue efficiency in {row['channel']}")

st.success("STL Intelligence Engine Active")

# =========================
# UPGRADE: CHANNEL RANKING
# =========================

st.subheader("🏆 Channel Ranking")

df["conversion"] = df["purchases"] / df["visitors"]
df["revenue_per_purchase"] = df["revenue"] / df["purchases"].replace(0, 1)
df["channel_score"] = (df["conversion"] * 0.7) + (df["revenue_per_purchase"] * 0.3 / 100)

ranked_df = df.sort_values("channel_score", ascending=False).reset_index(drop=True)
ranked_df["rank"] = ranked_df.index + 1

st.dataframe(
    ranked_df[["rank", "channel", "visitors", "purchases", "revenue", "conversion", "revenue_per_purchase", "channel_score"]],
    use_container_width=True
)

# =========================
# UPGRADE: SEVERITY ENGINE
# =========================

st.subheader("⚠️ Severity Assessment")

def severity_label(conv):
    if conv < 0.03:
        return "HIGH RISK"
    elif conv < 0.08:
        return "MEDIUM RISK"
    else:
        return "STABLE"

df["severity"] = df["conversion"].apply(severity_label)

for _, row in df.iterrows():
    if row["severity"] == "HIGH RISK":
        st.error(f"{row['channel']}: HIGH RISK — conversion is critically low.")
    elif row["severity"] == "MEDIUM RISK":
        st.warning(f"{row['channel']}: MEDIUM RISK — conversion needs improvement.")
    else:
        st.success(f"{row['channel']}: STABLE — conversion is healthy.")

# =========================
# UPGRADE: RECOMMENDATION ENGINE
# =========================

st.subheader("🧠 STL Recommendations")

for _, row in df.iterrows():
    conv = row["conversion"]
    rpp = row["revenue_per_purchase"]

    if conv < 0.03:
        st.write(f"**{row['channel']}** → Fix conversion pipeline immediately. Traffic exists, but users are not completing purchases.")
    elif conv < 0.08:
        st.write(f"**{row['channel']}** → Optimize checkout flow, offer quality, or targeting to raise conversion.")
    else:
        st.write(f"**{row['channel']}** → Maintain current process. This channel is performing well.")

    if rpp < 25:
        st.write(f"- {row['channel']} has low revenue efficiency. Increase order value or improve pricing strategy.")

# =========================
# UPGRADE: EXECUTIVE SUMMARY
# =========================

st.subheader("📌 Executive Summary")

weakest = df.loc[df["conversion"].idxmin(), "channel"]
strongest = df.loc[df["conversion"].idxmax(), "channel"]
avg_conversion = round(df["conversion"].mean() * 100, 2)

st.info(
    f"""
    STL Executive Summary:
    - Strongest channel: {strongest}
    - Weakest channel: {weakest}
    - Average conversion: {avg_conversion}%
    - Main issue: Pipeline inefficiency in low-converting channels
    - Primary action: Improve conversion process before increasing traffic
    """
)
