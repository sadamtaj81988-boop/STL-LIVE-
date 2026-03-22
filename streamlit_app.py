import streamlit as st
import pandas as pd

st.set_page_config(page_title="STL LIVE", layout="wide")

# =========================
# TITLE
# =========================
st.title("STL LIVE — Structured Intelligence Engine")
st.caption("Real-time business diagnostics and decision system")

# =========================
# INPUT MODE
# =========================
st.sidebar.header("STL Navigation")

mode = st.sidebar.radio(
    "Input Mode",
    ["Manual", "Demo Data", "Upload CSV"]
)

# =========================
# DATA INPUT
# =========================

def build_manual_df():
    st.subheader("Manual Inputs")

    store_v = st.number_input("Store Visitors", value=2000)
    online_v = st.number_input("Online Visitors", value=10000)
    market_v = st.number_input("Marketplace Visitors", value=3000)

    store_p = st.number_input("Store Purchases", value=400)
    online_p = st.number_input("Online Purchases", value=200)
    market_p = st.number_input("Marketplace Purchases", value=90)

    store_r = st.number_input("Store Revenue", value=12000)
    online_r = st.number_input("Online Revenue", value=8000)
    market_r = st.number_input("Marketplace Revenue", value=4500)

    data = {
        "channel": ["Store", "Online", "Marketplace"],
        "visitors": [store_v, online_v, market_v],
        "purchases": [store_p, online_p, market_p],
        "revenue": [store_r, online_r, market_r]
    }

    return pd.DataFrame(data)


def build_demo_df():
    data = {
        "channel": ["Store", "Online", "Marketplace"],
        "visitors": [2000, 10000, 3000],
        "purchases": [400, 200, 90],
        "revenue": [12000, 8000, 4500]
    }
    return pd.DataFrame(data)


def build_csv_df():
    file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
    if file:
        df = pd.read_csv(file)
        return df
    else:
        st.warning("Upload a CSV to continue")
        return None


# =========================
# SELECT DATA SOURCE
# =========================
if mode == "Manual":
    df = build_manual_df()
elif mode == "Demo Data":
    df = build_demo_df()
else:
    df = build_csv_df()

# Stop if no data
if df is None:
    st.stop()

# =========================
# CORE CALCULATIONS
# =========================
df["conversion"] = df["purchases"] / df["visitors"]
df["efficiency"] = df["revenue"] / df["purchases"].replace(0, 1)

# =========================
# VISUALIZATION
# =========================
st.subheader("Performance Overview")
st.line_chart(df.set_index("channel")[["conversion"]])

st.subheader("Raw Input")
st.dataframe(df, use_container_width=True)

# =========================
# HYDRO SCORE
# =========================
st.subheader("💧 STL Hydro Score")

hydro = (df["conversion"].mean() * 0.6) + (df["efficiency"].mean() * 0.4)
st.metric("Hydro Score", round(hydro, 2))

# =========================
# ALERTS
# =========================
st.subheader("🚨 STL Alerts")

alerts_triggered = False

for _, row in df.iterrows():
    if row["conversion"] < 0.03:
        st.error(f"Critical: {row['channel']} conversion extremely low")
        alerts_triggered = True
    elif row["conversion"] < 0.08:
        st.warning(f"Weak conversion in {row['channel']}")
        alerts_triggered = True

if not alerts_triggered:
    st.success("All channels operating normally")

# =========================
# CHANNEL RANKING
# =========================
st.subheader("🏆 Channel Ranking")

df["channel_score"] = (df["conversion"] * 0.7) + (df["efficiency"] * 0.3 / 100)

ranked = df.sort_values("channel_score", ascending=False).reset_index(drop=True)
ranked["rank"] = ranked.index + 1

st.dataframe(ranked, use_container_width=True)

# =========================
# SEVERITY ENGINE
# =========================
st.subheader("⚠️ Severity Assessment")

def severity(conv):
    if conv < 0.03:
        return "HIGH RISK"
    elif conv < 0.08:
        return "MEDIUM RISK"
    else:
        return "STABLE"

df["severity"] = df["conversion"].apply(severity)

for _, row in df.iterrows():
    if row["severity"] == "HIGH RISK":
        st.error(f"{row['channel']} → HIGH RISK")
    elif row["severity"] == "MEDIUM RISK":
        st.warning(f"{row['channel']} → MEDIUM RISK")
    else:
        st.success(f"{row['channel']} → STABLE")

# =========================
# RECOMMENDATIONS
# =========================
st.subheader("🧠 STL Recommendations")

for _, row in df.iterrows():
    if row["conversion"] < 0.03:
        st.write(f"{row['channel']}: Fix conversion pipeline immediately.")
    elif row["conversion"] < 0.08:
        st.write(f"{row['channel']}: Optimize funnel and checkout.")
    else:
        st.write(f"{row['channel']}: Performing well.")

    if row["efficiency"] < 25:
        st.write(f"- {row['channel']}: Increase revenue per purchase.")

# =========================
# EXECUTIVE SUMMARY
# =========================
st.subheader("📌 Executive Summary")

weakest = df.loc[df["conversion"].idxmin(), "channel"]
strongest = df.loc[df["conversion"].idxmax(), "channel"]

st.info(f"""
Strongest Channel: {strongest}
Weakest Channel: {weakest}
Core Problem: Conversion inefficiency
Action: Improve pipeline before increasing traffic
""")

# =========================
# SNAPSHOT
# =========================
st.subheader("📸 Snapshot")

if st.button("Save Snapshot"):
    st.success("Snapshot saved (mock feature)")

# =========================
# FINAL STATUS
# =========================
st.success("STL Intelligence Engine Active")
