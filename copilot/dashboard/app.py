import logging
from pathlib import Path
from typing import Dict, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from bootstrap import build_agent, build_intelligence, build_storage
from core import load_config, setup_logging


def _init() -> Dict:
    cfg = load_config("config.yaml")
    setup_logging(cfg["paths"]["log_path"])

    storage = build_storage(cfg)
    intelligence = build_intelligence(cfg, storage)
    agent = build_agent(cfg, intelligence)
    return {
        "cfg": cfg,
        "storage": storage,
        "intelligence": intelligence,
        "agent": agent,
    }


def _kpi_cards(df: pd.DataFrame) -> None:
    if df.empty:
        st.warning("No data found for selected filters.")
        return

    total_energy = df["energy_kwh"].sum()
    total_cost = df["cost_inr"].sum()
    total_runtime = df["runtime_minutes"].sum()
    total_idle = df["idle_minutes"].sum()
    total_possible = (df["period_hours"].sum()) * 60
    idle_waste_pct = (total_idle / total_possible) if total_possible else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Energy (kWh)", f"{total_energy:,.2f}")
    c2.metric("Total Cost (INR)", f"{total_cost:,.2f}")
    c3.metric("Runtime (min)", f"{total_runtime:,.0f}")
    c4.metric("Idle Waste %", f"{idle_waste_pct * 100:.2f}%")


# ---------- CHARTS UNCHANGED ----------


def _monthly_energy_chart(storage, machine_id: str, start_ts, end_ts):
    monthly = storage.query(machine_id, start_ts, end_ts, "M")
    if monthly.empty:
        st.info("No monthly data to render energy bar chart.")
        return
    fig = px.bar(
        monthly,
        x="timestamp",
        y="energy_kwh",
        color="machine_id",
        barmode="group",
        title="Monthly Energy Consumption",
    )
    st.plotly_chart(fig, use_container_width=True)


def _cost_trend(df: pd.DataFrame, granularity: str):
    if df.empty:
        return
    fig = px.line(
        df,
        x="timestamp",
        y="cost_inr",
        color="machine_id",
        title=f"Cost Trend ({granularity})",
    )
    st.plotly_chart(fig, use_container_width=True)


def _power_trend_with_anomalies(df_hourly: pd.DataFrame, anomalies: List[Dict]):
    if df_hourly.empty:
        return

    fig = px.line(
        df_hourly,
        x="timestamp",
        y="power_kw",
        color="machine_id",
        title="Power Trend with Anomaly Markers",
    )

    marker_rows = [a for a in anomalies if a.get("metric") == "power_kw"]
    if marker_rows:
        points = pd.DataFrame(marker_rows)
        points["timestamp"] = pd.to_datetime(points["timestamp"])
        fig.add_trace(
            go.Scatter(
                x=points["timestamp"],
                y=points["value"],
                mode="markers",
                marker=dict(color="red", size=7),
                name="Power Anomaly",
            )
        )

    st.plotly_chart(fig, use_container_width=True)


def _pressure_trend(df_hourly: pd.DataFrame, pmin: float, pmax: float):
    if df_hourly.empty:
        return

    fig = px.line(
        df_hourly,
        x="timestamp",
        y="pressure_bar",
        color="machine_id",
        title="Pressure Trend",
    )

    x_min = df_hourly["timestamp"].min()
    x_max = df_hourly["timestamp"].max()
    fig.add_shape(
        type="rect",
        x0=x_min,
        x1=x_max,
        y0=pmin,
        y1=pmax,
        fillcolor="green",
        opacity=0.1,
        line_width=0,
    )
    st.plotly_chart(fig, use_container_width=True)


def _runtime_distribution(df: pd.DataFrame):
    if df.empty:
        return

    values = [
        df["runtime_minutes"].sum(),
        df["idle_minutes"].sum(),
        df["downtime_minutes"].sum(),
    ]
    labels = ["Runtime", "Idle", "Downtime"]
    fig = px.pie(values=values, names=labels, title="Runtime Distribution")
    st.plotly_chart(fig, use_container_width=True)


def _anomaly_heatmap(df_hourly: pd.DataFrame, anomalies: List[Dict]):
    if df_hourly.empty or not anomalies:
        st.info("No anomalies to render heatmap.")
        return

    data = pd.DataFrame(anomalies)
    data["timestamp"] = pd.to_datetime(data["timestamp"])
    data["day"] = data["timestamp"].dt.date
    data["hour"] = data["timestamp"].dt.hour
    pivot = data.pivot_table(index="day", columns="hour", values="metric", aggfunc="count", fill_value=0)

    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=[str(x) for x in pivot.index],
            colorscale="Reds",
        )
    )
    fig.update_layout(title="Anomaly Heatmap (Day vs Hour)", xaxis_title="Hour", yaxis_title="Day")
    st.plotly_chart(fig, use_container_width=True)


# ---------- MAIN ----------


def main():
    services = _init()
    cfg = services["cfg"]
    storage = services["storage"]
    intelligence = services["intelligence"]
    copilot = services["agent"]

    st.set_page_config(page_title=cfg["dashboard"]["title"], layout="wide")
    st.title(cfg["dashboard"]["title"])

    if not Path(cfg["paths"]["db_path"]).exists():
        st.error("factory.db not found. Run `python main.py` first.")
        st.stop()

    machines_df = storage.list_machines()
    machines = ["ALL"] + machines_df["machine_id"].tolist()

    df_hourly_all = storage.query("ALL", None, None, "H")
    if df_hourly_all.empty:
        st.error("No hourly telemetry available.")
        st.stop()

    min_date = df_hourly_all["timestamp"].min().date()
    max_date = df_hourly_all["timestamp"].max().date()

    with st.sidebar:
        st.header("Controls")
        machine = st.selectbox("Machine", machines, index=0)
        date_range = st.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )
        granularity = st.radio("Granularity", ["H", "D", "W", "M", "Y"], index=1, horizontal=True)

    # -------- FIXED DATE HANDLING (ROBUST) --------

    if isinstance(date_range, tuple):
        start_date = date_range[0]
        end_date = date_range[1]
    else:
        start_date = date_range
        end_date = date_range

    start_ts = pd.Timestamp(start_date)
    end_ts = pd.Timestamp(end_date) + pd.Timedelta(hours=23, minutes=59, seconds=59)

    # ---------------------------------------------

    df = storage.query(machine, start_ts, end_ts, granularity)
    df_hourly = storage.query(machine, start_ts, end_ts, "H")

    anomaly_result = intelligence.anomalies(machine, start_ts, end_ts)
    anomalies = anomaly_result.get("result", {}).get("anomalies", [])

    _kpi_cards(df)

    col1, col2 = st.columns(2)
    with col1:
        _monthly_energy_chart(storage, machine, start_ts, end_ts)
    with col2:
        _cost_trend(df, granularity)

    col3, col4 = st.columns(2)
    with col3:
        _power_trend_with_anomalies(df_hourly, anomalies)
    with col4:
        pmin = float(cfg["intelligence"]["anomaly"]["pressure_min_bar"])
        pmax = float(cfg["intelligence"]["anomaly"]["pressure_max_bar"])
        _pressure_trend(df_hourly, pmin, pmax)

    col5, col6 = st.columns(2)
    with col5:
        _runtime_distribution(df)
    with col6:
        _anomaly_heatmap(df_hourly, anomalies)

    st.subheader("AI Chat Panel")

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_msg = st.chat_input("Ask about historical trends, anomalies, forecast, optimization, or what-if scenarios")

    if user_msg:
        st.session_state["chat_history"].append({"role": "user", "content": user_msg})
        with st.chat_message("user"):
            st.markdown(user_msg)

        result = copilot.ask(
            user_query=user_msg,
            machine_id=machine,
            start_ts=start_ts,
            end_ts=end_ts,
            granularity=granularity,
            compare_machine=None,
            forecast_days=90,
            whatif_inputs={},
        )

        assistant_text = result["answer"]

        st.session_state["chat_history"].append({"role": "assistant", "content": assistant_text})
        with st.chat_message("assistant"):
            st.markdown(assistant_text)


if __name__ == "__main__":
    main()
