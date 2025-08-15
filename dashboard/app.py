import time
import requests
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Token Bucket Dashboard", layout="wide")

API = st.secrets.get("API_URL", "http://localhost:8000")

st.title("Live Traffic: Token Bucket Effectiveness")
window_options = {
    "30s": 30,
    "1m": 60,
    "5m": 300,
    "10m": 600,
}
window_label = st.sidebar.selectbox("Window", list(window_options.keys()), index=1)
window_seconds = window_options[window_label]

placeholder1 = st.empty()
placeholder2 = st.empty()

def fetch_points():
    try:
        r = requests.get(f"{API}/metrics", timeout=2)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Failed to fetch metrics: {e}")
        return {"points": [], "capacity": 0, "rate": 0}

while True:
    data = fetch_points()
    pts = data.get("points", [])
    if pts:
        df = pd.DataFrame(pts)
        df["time"] = pd.to_datetime(df["ts"], unit="s")
        # Filter by window
        now = pd.Timestamp.now()
        df = df[df["time"] >= now - pd.Timedelta(seconds=window_seconds)]
        # Cards
        allowed = int(df["allowed"].sum())
        blocked = int(df["blocked"].sum())
        tokens_now = float(df.iloc[-1]["tokens"]) if not df.empty else 0.0
        c1, c2, c3 = placeholder1.columns(3)
        c1.metric(f"Allowed ({window_label})", allowed)
        c2.metric(f"Blocked ({window_label})", blocked)
        c3.metric("Tokens (latest)", f"{tokens_now:.2f}", help="Remaining tokens in recent bucket")
        # Chart
        if not df.empty:
            df2 = df.groupby("time", as_index=False)[["allowed", "blocked"]].sum()
            fig = px.line(df2, x="time", y=["allowed", "blocked"], title=f"Allowed vs Blocked ({window_label})")
            unique_key = f"plotly_{window_label}_{int(time.time()*1000)}"
            placeholder2.plotly_chart(fig, use_container_width=True, key=unique_key)
        else:
            placeholder2.write("No data for selected window.")
    else:
        placeholder1.write("Waiting for metrics...")
        placeholder2.empty()
    time.sleep(1)
