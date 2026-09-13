import argparse
import json
import os
import urllib.request
from pathlib import Path

import snowflake.connector


ROOT = Path(__file__).resolve().parents[1]


def env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value


def load_labelled(path: str):
    with open(path, encoding="utf-8-sig") as f:
        return [json.loads(line) for line in f if line.strip()]


def connect_to_snowflake():
    required = [
        "SNOWFLAKE_USER",
        "SNOWFLAKE_PASSWORD",
        "SNOWFLAKE_ACCOUNT",
        "SNOWFLAKE_WAREHOUSE",
    ]
    missing = [name for name in required if env(name) is None]
    if missing:
        raise RuntimeError(
            "Missing required Snowflake environment variables: "
            + ", ".join(missing)
            + "."
        )

    database = env("SNOWFLAKE_DATABASE", "FIRMABLE_SALES_INTELLIGENCE")
    schema = env("SNOWFLAKE_SCHEMA", "FEATURES")

    return snowflake.connector.connect(
        user=env("SNOWFLAKE_USER"),
        password=env("SNOWFLAKE_PASSWORD"),
        account=env("SNOWFLAKE_ACCOUNT"),
        warehouse=env("SNOWFLAKE_WAREHOUSE"),
        database=database,
        schema=schema,
    )


def fetch_evidence_for_accounts(account_keys):
    conn = connect_to_snowflake()
    try:
        placeholders = ", ".join(["%s"] * len(account_keys))
        sql = f"""
            SELECT *
            FROM FIRMABLE_SALES_INTELLIGENCE.FEATURES.ACCOUNT_EVIDENCE
            WHERE ACCOUNT_KEY IN ({placeholders})
            ORDER BY PRIORITY_SCORE DESC
        """
        cur = conn.cursor()
        cur.execute(sql, tuple(account_keys))
        cols = [col[0] for col in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]
        cur.close()
        return rows
    finally:
        conn.close()


def normalize_account_key(value: str) -> str:
    return value.strip().casefold()


def build_prompt(template_text: str, evidence: dict) -> str:
    return template_text.replace("{{ACCOUNT_DATA}}", json.dumps(evidence, default=str, ensure_ascii=False))


def call_ollama(prompt: str, model: str, base_url: str):
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


def to_jsonable(value):
    if isinstance(value, dict):
        return {str(key): to_jsonable(val) for key, val in value.items()}
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if hasattr(value, "to_python"):
        try:
            return value.to_python()
        except Exception:
            pass
    if hasattr(value, "__float__") and not isinstance(value, bool):
        try:
            return float(value)
        except Exception:
            pass
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def save_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(to_jsonable(payload), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="evals/labelled_accounts_template.jsonl")
    parser.add_argument("--output-dir", default="evals/results")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--model", default=env("OLLAMA_MODEL", "llama3.1:8b"))
    parser.add_argument("--base-url", default=env("OLLAMA_BASE_URL", "http://localhost:11434"))
    args = parser.parse_args()

    labelled_rows = load_labelled(args.input)
    if args.limit is not None:
        labelled_rows = labelled_rows[: args.limit]

    account_keys = [row["account_key"] for row in labelled_rows]
    evidence_rows = fetch_evidence_for_accounts(account_keys)

    evidence_by_key = {
        normalize_account_key(row["ACCOUNT_KEY"]): row
        for row in evidence_rows
    }

    missing = []
    for row in labelled_rows:
        if normalize_account_key(row["account_key"]) not in evidence_by_key:
            missing.append(row["account_key"])
    if missing:
        raise RuntimeError(
            "Could not find these accounts in ACCOUNT_EVIDENCE: "
            + ", ".join(missing)
        )

    prompt_versions = {
        "v1": (ROOT / "prompts/account_brief/v1.md").read_text(encoding="utf-8"),
        "v2": (ROOT / "prompts/account_brief/v2.md").read_text(encoding="utf-8"),
    }

    summary = []
    for version, template_text in prompt_versions.items():
        version_dir = Path(args.output_dir) / version
        version_dir.mkdir(parents=True, exist_ok=True)

        for row in labelled_rows:
            account_key = row["account_key"]
            evidence = evidence_by_key[normalize_account_key(account_key)]
            prompt = build_prompt(template_text, evidence)

            response = call_ollama(prompt, args.model, args.base_url)
            payload = {
                "account_key": account_key,
                "expected_priority": row.get("expected_priority"),
                "prompt_version": version,
                "model": args.model,
                "response": response,
                "evidence": evidence,
            }
            save_json(version_dir / f"{account_key}.json", payload)
            summary.append(
                {
                    "prompt_version": version,
                    "account_key": account_key,
                    "saved_to": str(version_dir / f"{account_key}.json"),
                }
            )

    print(json.dumps({"generated": summary}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
