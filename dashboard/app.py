"""Streamlit dashboard for the DevOps Monitor.

Run the API first (uvicorn api.main:app --port 8000), then:
    streamlit run dashboard/app.py
"""

import time

import httpx
import pandas as pd
import streamlit as st

# ─── Config ───────────────────────────────────────────────────────────────────

API_BASE = "http://localhost:8000"
DEFAULT_KEY = "demo-key"
MAX_POINTS = 60

st.set_page_config(page_title="DevOps Monitor", page_icon="🖥️", layout="wide")


# ─── Cached fetchers ──────────────────────────────────────────────────────────

@st.cache_data(ttl=2)
def fetch_metrics() -> dict:
    """Fetch the live metrics snapshot (cached 2s)."""
    try:
        r = httpx.get(f"{API_BASE}/metrics", timeout=3.0)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


@st.cache_data(ttl=5)
def fetch_servers() -> list[dict] | str:
    """Fetch the server list (cached 5s). Returns an error string on failure."""
    try:
        r = httpx.get(f"{API_BASE}/servers", timeout=3.0)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return str(e)


# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("⚙️  Settings")
    if "api_key" not in st.session_state:
        st.session_state.api_key = DEFAULT_KEY
    st.session_state.api_key = st.text_input(
        "API Key", value=st.session_state.api_key, type="password"
    )
    refresh_interval = st.slider("Auto-refresh (s)", 1, 30, 2)


# ─── Header ───────────────────────────────────────────────────────────────────

st.title("🖥️  DevOps Monitor")
tab_metrics, tab_servers = st.tabs(["📊  Metrics", "🗄️  Servers"])


# ─── Tab 1 — Metrics ──────────────────────────────────────────────────────────

with tab_metrics:
    data = fetch_metrics()

    if "error" in data:
        st.error(f"Cannot reach API: {data['error']}")
        st.info("Start it with `uvicorn api.main:app --reload --port 8000`.")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("CPU", f"{data['cpu_percent']:.1f}%")
        col2.metric(
            "Memory",
            f"{data['memory_percent']:.1f}%",
            f"{data['memory_used_gb']:.1f} / {data['memory_total_gb']:.1f} GB",
        )
        col3.metric("Disk", f"{data['disk_percent']:.1f}%")

        # Accumulate the last MAX_POINTS samples in session_state.
        if "history" not in st.session_state:
            st.session_state.history = []
        st.session_state.history.append(
            {
                "cpu_percent": data["cpu_percent"],
                "memory_percent": data["memory_percent"],
            }
        )
        st.session_state.history = st.session_state.history[-MAX_POINTS:]

        df = pd.DataFrame(st.session_state.history)
        st.line_chart(df, height=250)
        st.caption(f"Last {len(df)} samples of CPU & memory")


# ─── Tab 2 — Servers ──────────────────────────────────────────────────────────

def _color_status(val: str) -> str:
    colors = {"UP": "#1b5e20", "DEGRADED": "#b26a00", "DOWN": "#7f1d1d"}
    bg = colors.get(val, "#444444")
    return f"background-color: {bg}; color: white;"


with tab_servers:
    servers = fetch_servers()

    if isinstance(servers, str):
        st.error(f"Could not load servers: {servers}")
    elif not servers:
        st.info("No servers registered yet — use the form below.")
    else:
        df = pd.DataFrame(servers)[["id", "name", "host", "port", "status"]]
        st.dataframe(
            df.style.map(_color_status, subset=["status"]),
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    # Registration form — st.form prevents reruns on each keystroke.
    st.subheader("➕  Register a server")
    with st.form("register_form", clear_on_submit=True):
        name = st.text_input("Name", placeholder="api-prod")
        host = st.text_input("Host", placeholder="localhost")
        port = st.number_input("Port", min_value=1, max_value=65535, value=8080)
        submitted = st.form_submit_button("Register")

    if submitted:
        if not name or not host:
            st.error("Name and host are required.")
        else:
            try:
                r = httpx.post(
                    f"{API_BASE}/servers",
                    json={"name": name, "host": host, "port": int(port)},
                    headers={"X-API-Key": st.session_state.api_key},
                    timeout=5.0,
                )
                if r.status_code == 201:
                    st.success(f"Registered '{name}' (id={r.json()['id']})")
                    fetch_servers.clear()
                else:
                    st.error(f"Error {r.status_code}: {r.text}")
            except Exception as e:
                st.error(str(e))

    # On-demand health check.
    if isinstance(servers, list) and servers:
        st.subheader("🔄  Run a health check")
        names = {s["id"]: f"[{s['id']}] {s['name']}" for s in servers}
        sel_id = st.selectbox(
            "Server", list(names), format_func=lambda i: names[i]
        )
        if st.button("Check now"):
            try:
                r = httpx.post(f"{API_BASE}/servers/{sel_id}/check", timeout=5.0)
                if r.status_code == 202:
                    st.success("Check scheduled — refreshing…")
                    fetch_servers.clear()
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error(f"Error {r.status_code}: {r.text}")
            except Exception as e:
                st.error(str(e))


# ─── Live-refresh loop ────────────────────────────────────────────────────────

placeholder = st.empty()
with placeholder.container():
    st.caption(f"⏱ Auto-refreshing every {refresh_interval}s — {time.strftime('%H:%M:%S')}")

time.sleep(refresh_interval)
st.rerun()
