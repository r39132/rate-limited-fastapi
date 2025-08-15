
import time
import requests
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Token Bucket Dashboard", layout="wide")

API = st.secrets.get("API_URL", "http://localhost:8000")

st.title("Live Traffic: Token Bucket Effectiveness")
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
        # Cards
        allowed = int(df["allowed"].sum())
        blocked = int(df["blocked"].sum())
        tokens_now = float(df.iloc[-1]["tokens"])
        c1, c2, c3 = placeholder1.columns(3)
        c1.metric("Allowed (window)", allowed)
        c2.metric("Blocked (window)", blocked)
        c3.metric("Tokens (latest)", f"{tokens_now:.2f}", help="Remaining tokens in recent bucket")
        # Chart
        df2 = df.groupby("time", as_index=False)[["allowed", "blocked"]].sum()
        fig = px.line(df2, x="time", y=["allowed", "blocked"], title="Allowed vs Blocked (per second)")
        placeholder2.plotly_chart(fig, use_container_width=True)
    else:
        placeholder1.write("Waiting for metrics...")
        placeholder2.empty()
    time.sleep(1)
