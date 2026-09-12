import json
import os
import streamlit as st
import pandas as pd
import requests
import snowflake.connector

st.set_page_config(page_title="CyberSignal Cloud", page_icon="🛡️", layout="wide")

DEFAULT_AI_MODEL = "meta-llama/llama-3.1-8b-instruct:free"
DEFAULT_AI_BASE_URL = "https://openrouter.ai/api/v1"


def get_secret(section: str, key: str, env_name: str | None = None, default: str | None = None):
    try:
        if section in st.secrets:
            value = st.secrets[section][key]
            if value not in (None, ""):
                return value
    except Exception:
        pass

    if env_name:
        value = os.getenv(env_name)
        if value not in (None, ""):
            return value

    return default


@st.cache_resource
def connect_to_snowflake():
    user = get_secret("snowflake", "user", "SNOWFLAKE_USER")
    password = get_secret("snowflake", "password", "SNOWFLAKE_PASSWORD")
    account = get_secret("snowflake", "account", "SNOWFLAKE_ACCOUNT")
    warehouse = get_secret("snowflake", "warehouse", "SNOWFLAKE_WAREHOUSE")
    database = get_secret("snowflake", "database", "SNOWFLAKE_DATABASE", "FIRMABLE_SALES_INTELLIGENCE")
    schema = get_secret("snowflake", "schema", "SNOWFLAKE_SCHEMA", "FEATURES")

    missing = []
    for name, value in {
        "SNOWFLAKE_USER": user,
        "SNOWFLAKE_PASSWORD": password,
        "SNOWFLAKE_ACCOUNT": account,
        "SNOWFLAKE_WAREHOUSE": warehouse,
    }.items():
        if value in (None, ""):
            missing.append(name)

    if missing:
        st.error(
            "Missing Snowflake configuration. Add these in Streamlit Cloud secrets or set env vars: "
            + ", ".join(missing)
        )
        st.stop()

    return snowflake.connector.connect(
        user=user,
        password=password,
        account=account,
        warehouse=warehouse,
        database=database,
        schema=schema,
    )


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


def call_ai(prompt: str) -> str:
    api_key = get_secret("ai", "api_key", "AI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing AI API key. Add [ai] api_key in Streamlit Cloud secrets.")

    model = get_secret("ai", "model", "AI_MODEL", DEFAULT_AI_MODEL)
    base_url = get_secret("ai", "base_url", "AI_BASE_URL", DEFAULT_AI_BASE_URL)

    endpoint = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
    }

    response = requests.post(endpoint, headers=headers, json=payload, timeout=120)
    response.raise_for_status()

    data = response.json()
    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError(f"AI provider returned no content. Response: {data}")

    message = choices[0].get("message", {})
    content = message.get("content", "")
    if isinstance(content, list):
        content = "\n".join(part.get("text", "") for part in content if isinstance(part, dict))

    if not content:
        raise RuntimeError(f"AI provider returned empty content. Response: {data}")

    return content


st.title("🛡️ CyberSignal Cloud")
st.caption("Streamlit Community Cloud UI for Snowflake-backed AI sales intelligence")

if not get_secret("ai", "api_key", "AI_API_KEY"):
    st.warning(
        "AI API key is not configured yet. Add [ai] api_key in Streamlit Cloud secrets or set AI_API_KEY."
    )

conn = None
try:
    conn = connect_to_snowflake()
except Exception as exc:
    st.error(f"Failed to connect to Snowflake: {exc}")
    st.stop()

st.sidebar.subheader("Configuration")
st.sidebar.write("Snowflake secrets: [snowflake] user, password, account, warehouse")
st.sidebar.write("AI secrets: [ai] api_key, model, base_url")

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

st.subheader(str(account_row["ORGANIZATION"] or selected_account))
col_a, col_b, col_c = st.columns(3)
col_a.metric("Priority score", float(account_row["PRIORITY_SCORE"]))
col_b.metric("Risky services", int(account_row["RISKY_PORT_COUNT"]))
col_c.metric("Distinct IPs", int(account_row["DISTINCT_IPS"]))

st.markdown("### Evidence")

evidence = {
    "account_key": selected_account,
    "organization": str(account_row["ORGANIZATION"]),
    "priority": str(account_row["PRIORITY"]),
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

st.json(evidence)

if st.button("Generate AI account brief"):
    prompt = build_prompt(evidence)
    try:
        with st.spinner("Generating AI account brief..."):
            result = call_ai(prompt)
        st.session_state["brief"] = result
    except Exception as exc:
        st.error(f"AI generation failed: {exc}")

if "brief" in st.session_state:
    try:
        brief_obj = json.loads(st.session_state["brief"])
        st.markdown("### AI Brief")
        st.json(brief_obj)
    except Exception:
        st.markdown("### AI Brief")
        st.write(st.session_state["brief"])
