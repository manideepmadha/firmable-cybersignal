import json
import os
import time
import urllib.error
import urllib.request

import pandas as pd
import snowflake.connector
import streamlit as st

st.set_page_config(page_title="CyberSignal Local", page_icon="🛡️", layout="wide")


SESSION_NAME = "local_streamlit_app"


def env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value


@st.cache_resource
def connect_to_snowflake():
    user = env("SNOWFLAKE_USER")
    password = env("SNOWFLAKE_PASSWORD")
    account = env("SNOWFLAKE_ACCOUNT")
    warehouse = env("SNOWFLAKE_WAREHOUSE")

    missing = [
        key
        for key, value in {
            "SNOWFLAKE_USER": user,
            "SNOWFLAKE_PASSWORD": password,
            "SNOWFLAKE_ACCOUNT": account,
            "SNOWFLAKE_WAREHOUSE": warehouse,
        }.items()
        if value is None
    ]

    if missing:
        st.error(
            "Missing Snowflake environment variables: "
            + ", ".join(missing)
            + ".\nSet them before running this app."
        )
        st.stop()

    database = env("SNOWFLAKE_DATABASE", "FIRMABLE_SALES_INTELLIGENCE")
    schema = env("SNOWFLAKE_SCHEMA", "FEATURES")

    conn = snowflake.connector.connect(
        user=user,
        password=password,
        account=account,
        warehouse=warehouse,
        database=database,
        schema=schema,
    )
    return conn


def fetch_summary(conn):
    sql = """
        SELECT COUNT(*) ACCOUNTS,
               COUNT_IF(PRIORITY='HIGH') HIGH_ACCOUNTS,
               COUNT_IF(PRIORITY='MEDIUM') MEDIUM_ACCOUNTS,
               COUNT_IF(PRIORITY='LOW') LOW_ACCOUNTS
        FROM FIRMABLE_SALES_INTELLIGENCE.FEATURES.ACCOUNT_SCORES
    """
    cur = conn.cursor()
    cur.execute(sql)
    row = cur.fetchone()
    cur.close()
    return {
        "ACCOUNTS": int(row[0]),
        "HIGH_ACCOUNTS": int(row[1]),
        "MEDIUM_ACCOUNTS": int(row[2]),
        "LOW_ACCOUNTS": int(row[3]),
    }


def fetch_accounts(conn, priority: str):
    sql = """
        SELECT ACCOUNT_KEY, ORGANIZATION, PRIORITY_SCORE, PRIORITY,
               EVENT_COUNT, DISTINCT_IPS, DISTINCT_PORTS,
               RISKY_PORT_COUNT, REMOTE_ADMIN_COUNT,
               LEGACY_PROTOCOL_COUNT, TECHNOLOGY_SIGNAL_COUNT,
               CLOUD_EVENT_COUNT, LAST_SEEN
        FROM FIRMABLE_SALES_INTELLIGENCE.FEATURES.ACCOUNT_SCORES
        WHERE PRIORITY = %s
        ORDER BY PRIORITY_SCORE DESC
        LIMIT 100
    """
    cur = conn.cursor()
    cur.execute(sql, (priority,))
    rows = cur.fetchall()
    cur.close()

    columns = [
        "ACCOUNT_KEY",
        "ORGANIZATION",
        "PRIORITY_SCORE",
        "PRIORITY",
        "EVENT_COUNT",
        "DISTINCT_IPS",
        "DISTINCT_PORTS",
        "RISKY_PORT_COUNT",
        "REMOTE_ADMIN_COUNT",
        "LEGACY_PROTOCOL_COUNT",
        "TECHNOLOGY_SIGNAL_COUNT",
        "CLOUD_EVENT_COUNT",
        "LAST_SEEN",
    ]
    return pd.DataFrame(rows, columns=columns)


def fetch_account_by_key(conn, account_key: str):
    sql = """
        SELECT ACCOUNT_KEY, ORGANIZATION, PRIORITY_SCORE, PRIORITY,
               EVENT_COUNT, DISTINCT_IPS, DISTINCT_PORTS,
               RISKY_PORT_COUNT, REMOTE_ADMIN_COUNT,
               LEGACY_PROTOCOL_COUNT, TECHNOLOGY_SIGNAL_COUNT,
               CLOUD_EVENT_COUNT, LAST_SEEN
        FROM FIRMABLE_SALES_INTELLIGENCE.FEATURES.ACCOUNT_SCORES
        WHERE ACCOUNT_KEY = %s
    """
    cur = conn.cursor()
    cur.execute(sql, (account_key,))
    row = cur.fetchone()
    cur.close()
    if row is None:
        return None

    columns = [
        "ACCOUNT_KEY",
        "ORGANIZATION",
        "PRIORITY_SCORE",
        "PRIORITY",
        "EVENT_COUNT",
        "DISTINCT_IPS",
        "DISTINCT_PORTS",
        "RISKY_PORT_COUNT",
        "REMOTE_ADMIN_COUNT",
        "LEGACY_PROTOCOL_COUNT",
        "TECHNOLOGY_SIGNAL_COUNT",
        "CLOUD_EVENT_COUNT",
        "LAST_SEEN",
    ]
    return dict(zip(columns, row))


@st.cache_data(ttl=60)
def fetch_ollama_status():
    base_url = env("OLLAMA_BASE_URL", "http://localhost:11434")
    model = env("OLLAMA_MODEL", "llama3.1:8b")

    try:
        req = urllib.request.Request(
            f"{base_url}/api/tags",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.load(response)
            models = [item.get("name", "") for item in data.get("models", [])]
        return {
            "base_url": base_url,
            "model": model,
            "available": model in models,
            "models": models,
        }
    except Exception:
        return {
            "base_url": base_url,
            "model": model,
            "available": False,
            "models": [],
        }


def build_prompt(evidence: dict) -> str:
    return f"""You are a B2B cybersecurity sales intelligence analyst.
Use only ACCOUNT_DATA. Never invent breaches, incidents, employees, revenue,
funding, contacts, technologies or vulnerabilities. Separate facts from hypotheses.
Do not change the numeric score. Return valid JSON with summary,
observed_evidence, why_now, pain_hypotheses, recommended_buyer_personas,
outreach_angle, confidence and caveats.

ACCOUNT_DATA:
{json.dumps(evidence, default=str)}
"""


def call_ollama(prompt: str) -> str:
    base_url = env("OLLAMA_BASE_URL", "http://localhost:11434")
    model = env("OLLAMA_MODEL", "llama3.1:8b")

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }

    request = urllib.request.Request(
        f"{base_url}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )

    with urllib.request.urlopen(request, timeout=120) as response:
        data = json.load(response)
        return data.get("response", "")


st.title("🛡️ CyberSignal Local")
st.caption("Local Streamlit app for Snowflake-backed cybersecurity prospect scoring")

conn = None
try:
    conn = connect_to_snowflake()
except Exception as exc:
    st.error(f"Failed to connect to Snowflake: {exc}")
    st.stop()

st.sidebar.subheader("Configuration")
st.sidebar.write("Snowflake env vars: SNOWFLAKE_USER, SNOWFLAKE_PASSWORD, SNOWFLAKE_ACCOUNT, SNOWFLAKE_WAREHOUSE")
st.sidebar.write("Optional local AI env vars: OLLAMA_BASE_URL, OLLAMA_MODEL")

ollama_status = fetch_ollama_status()
if ollama_status["available"]:
    st.sidebar.success(f"Ollama model available: {ollama_status['model']}")
else:
    st.sidebar.warning(
        "Local AI is not available yet. Start Ollama and pull a model such as llama3.1:8b."
    )
    st.sidebar.write(f"Base URL: {ollama_status['base_url']}")
    st.sidebar.write(f"Expected model: {ollama_status['model']}")

summary = fetch_summary(conn)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Accounts", int(summary["ACCOUNTS"]))
col2.metric("High priority", int(summary["HIGH_ACCOUNTS"]))
col3.metric("Medium", int(summary["MEDIUM_ACCOUNTS"]))
col4.metric("Low", int(summary["LOW_ACCOUNTS"]))

priority = st.sidebar.selectbox("Priority", ["HIGH", "MEDIUM", "LOW"])
df = fetch_accounts(conn, priority)

st.subheader(f"{priority} prospect queue")
st.dataframe(df, use_container_width=True, hide_index=True)

if df.empty:
    st.info("No accounts match that priority.")
    st.stop()

selected_account = st.selectbox("Select account", df["ACCOUNT_KEY"].tolist())
account_row = fetch_account_by_key(conn, selected_account)

if account_row is None:
    st.error("Selected account was not found.")
    st.stop()

st.subheader(str(account_row["ORGANIZATION"] or selected_account))

metric_col1, metric_col2, metric_col3 = st.columns(3)
metric_col1.metric("Priority score", float(account_row["PRIORITY_SCORE"]))
metric_col2.metric("Risky services", int(account_row["RISKY_PORT_COUNT"]))
metric_col3.metric("Distinct IPs", int(account_row["DISTINCT_IPS"]))

st.markdown("### Evidence")
st.json(
    {
        "account_key": account_row["ACCOUNT_KEY"],
        "organization": account_row["ORGANIZATION"],
        "priority": account_row["PRIORITY"],
        "priority_score": float(account_row["PRIORITY_SCORE"]),
        "event_count": int(account_row["EVENT_COUNT"]),
        "distinct_ips": int(account_row["DISTINCT_IPS"]),
        "distinct_ports": int(account_row["DISTINCT_PORTS"]),
        "risky_port_count": int(account_row["RISKY_PORT_COUNT"]),
        "remote_admin_count": int(account_row["REMOTE_ADMIN_COUNT"]),
        "legacy_protocol_count": int(account_row["LEGACY_PROTOCOL_COUNT"]),
        "technology_signal_count": int(account_row["TECHNOLOGY_SIGNAL_COUNT"]),
        "cloud_event_count": int(account_row["CLOUD_EVENT_COUNT"]),
        "last_seen": str(account_row["LAST_SEEN"]),
    }
)

if st.button("Generate local AI account brief"):
    if not ollama_status["available"]:
        st.warning("Ollama is not running or the configured model is not available.")
        st.info("Start Ollama and run: ollama pull llama3.1:8b")
    else:
        prompt = build_prompt(
            {
                "account_key": account_row["ACCOUNT_KEY"],
                "organization": account_row["ORGANIZATION"],
                "priority": account_row["PRIORITY"],
                "priority_score": float(account_row["PRIORITY_SCORE"]),
                "event_count": int(account_row["EVENT_COUNT"]),
                "distinct_ips": int(account_row["DISTINCT_IPS"]),
                "distinct_ports": int(account_row["DISTINCT_PORTS"]),
                "risky_port_count": int(account_row["RISKY_PORT_COUNT"]),
                "remote_admin_count": int(account_row["REMOTE_ADMIN_COUNT"]),
                "legacy_protocol_count": int(account_row["LEGACY_PROTOCOL_COUNT"]),
                "technology_signal_count": int(account_row["TECHNOLOGY_SIGNAL_COUNT"]),
                "cloud_event_count": int(account_row["CLOUD_EVENT_COUNT"]),
                "last_seen": str(account_row["LAST_SEEN"]),
            }
        )

        start_time = time.perf_counter()
        try:
            response = call_ollama(prompt)
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            st.session_state["brief_response"] = response
            st.session_state["brief_latency_ms"] = latency_ms
        except Exception as exc:
            st.error(f"Failed to generate local AI brief: {exc}")

if "brief_response" in st.session_state:
    st.markdown("### Local AI brief")
    st.caption(f"Generated in {st.session_state.get('brief_latency_ms', 0)} ms")
    try:
        st.json(json.loads(st.session_state["brief_response"]))
    except Exception:
        st.write(st.session_state["brief_response"])
