import time
from typing import Any

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

st.set_page_config(page_title="Token Bucket Dashboard", layout="wide")
API = st.secrets.get("API_URL", "http://localhost:8000")

st.title("Token Bucket Dashboard")

WINDOW_OPTIONS: dict[str, int] = {
    "30s": 30,
    "1m": 60,
    "5m": 5 * 60,
    "10m": 10 * 60,
    "30m": 30 * 60,
}
side = st.sidebar
window_label = side.selectbox("Window", list(WINDOW_OPTIONS.keys()), index=2)
window_seconds = WINDOW_OPTIONS[window_label]

auto_refresh = side.checkbox("Auto refresh", True)
refresh_every = side.slider("Refresh interval (s)", 1, 5, 1)


def fetch_points() -> dict[str, Any]:
    try:
        r = requests.get(f"{API}/metrics", timeout=2)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Failed to fetch metrics: {e}")
        return {"points": []}


data = fetch_points()
points: list[dict[str, Any]] = data.get("points", [])
capacity = data.get("capacity")
rate = data.get("rate")

side.markdown(
    f"**Bucket capacity:** {capacity}<br/>**Refill rate:** {rate} tokens/sec",
    unsafe_allow_html=True,
)

if not points:
    st.info("No metrics yet.")
else:
    df = pd.DataFrame(points)
    # ts, allowed, blocked, tokens, latency_ms
    df["time"] = pd.to_datetime(df["ts"], unit="s", utc=True)

    now = pd.Timestamp.now(tz="UTC")
    cutoff = now - pd.Timedelta(seconds=window_seconds)
    df_window = df[df["time"] >= cutoff].copy()

    if df_window.empty:
        st.warning(f"No data inside last {window_label}.")
    else:
        # KPIs
        allowed_sum = int(df_window["allowed"].sum())
        blocked_sum = int(df_window["blocked"].sum())
        latest_tokens = float(df_window.iloc[-1]["tokens"])
        c1, c2, c3 = st.columns(3)
        c1.metric(f"Allowed ({window_label})", allowed_sum)
        c2.metric(f"Blocked ({window_label})", blocked_sum)
        c3.metric("Tokens (latest)", f"{latest_tokens:.2f}")
        st.caption(f"Capacity: {capacity} | Rate: {rate} tokens/sec")

        # Per-second aggregation for allowed/blocked
        df_sec = (
            df_window.assign(sec=df_window["time"].dt.floor("s"))
            .groupby("sec", as_index=False)[["allowed", "blocked"]]
            .sum()
        )

        # Counts chart
        fig = px.line(
            df_sec,
            x="sec",
            y=["allowed", "blocked"],
            title=f"Allowed vs Blocked (window {window_label})",
        )
        fig.update_xaxes(range=[cutoff, now])
        st.plotly_chart(fig, use_container_width=True)

        # Token balance
        fig2 = px.line(
            df_window,
            x="time",
            y="tokens",
            title=f"Token Balance (window {window_label})",
        )
        fig2.update_xaxes(range=[cutoff, now])
        st.plotly_chart(fig2, use_container_width=True)

        # Latency quantiles (allowed requests with latency)
        lat_df = df_window[(df_window["allowed"] == 1) & df_window["latency_ms"].notna()].copy()
        if lat_df.empty:
            st.info("No latency samples yet in window.")
        else:
            lat_df["sec"] = lat_df["time"].dt.floor("s")
            q = (
                lat_df.groupby("sec")["latency_ms"]
                .agg(
                    p50=lambda s: s.quantile(0.50),
                    p95=lambda s: s.quantile(0.95),
                    p99=lambda s: s.quantile(0.99),
                    max="max",
                )
                .reset_index()
            )
            # Melt for plotting
            q_melt = q.melt(id_vars="sec", var_name="quantile", value_name="ms")
            fig3 = px.line(
                q_melt,
                x="sec",
                y="ms",
                color="quantile",
                title=f"Latency (p50/p95/p99/max) (window {window_label})",
            )
            fig3.update_yaxes(title="Latency (ms)")
            fig3.update_xaxes(range=[cutoff, now])
            st.plotly_chart(fig3, use_container_width=True)

        st.caption(
            f"Rows in raw window: {len(df_window)} | First: "
            f"{df_window['time'].min()} | Cutoff: {cutoff}"
        )

st.caption("Latency chart shows quantiles for allowed requests only.")

if auto_refresh:
    time.sleep(refresh_every)
    st.rerun()
