import argparse
import json
import os
import sys

import snowflake.connector


def load_labelled(path: str):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def normalize_account_key(value: str) -> str:
    return value.strip().casefold()


def connect_to_snowflake():
    required = [
        "SNOWFLAKE_USER",
        "SNOWFLAKE_PASSWORD",
        "SNOWFLAKE_ACCOUNT",
        "SNOWFLAKE_WAREHOUSE",
    ]

    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise RuntimeError(
            "Missing required Snowflake environment variables: "
            + ", ".join(missing)
            + ". Set them before running this script."
        )

    database = os.getenv("SNOWFLAKE_DATABASE", "FIRMABLE_SALES_INTELLIGENCE")
    schema = os.getenv("SNOWFLAKE_SCHEMA", "FEATURES")

    return snowflake.connector.connect(
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        database=database,
        schema=schema,
    )


def fetch_predictions_from_snowflake(account_keys):
    conn = connect_to_snowflake()
    try:
        placeholders = ", ".join(["%s"] * len(account_keys))
        sql = f"""
            SELECT ACCOUNT_KEY, PRIORITY
            FROM FIRMABLE_SALES_INTELLIGENCE.FEATURES.ACCOUNT_SCORES
            WHERE ACCOUNT_KEY IN ({placeholders})
        """
        cur = conn.cursor()
        cur.execute(sql, tuple(account_keys))
        rows = cur.fetchall()
        cur.close()
    finally:
        conn.close()

    mapping = {}
    for account_key, priority in rows:
        mapping[normalize_account_key(account_key)] = priority

    return mapping


def write_predictions(input_path: str, output_path: str):
    labelled_rows = load_labelled(input_path)

    account_keys = [row["account_key"] for row in labelled_rows]
    predictions_map = fetch_predictions_from_snowflake(account_keys)

    missing_accounts = []
    output_rows = []
    for row in labelled_rows:
        account_key = row["account_key"]
        normalized = normalize_account_key(account_key)
        if normalized not in predictions_map:
            missing_accounts.append(account_key)
            continue

        output_rows.append(
            {
                "account_key": account_key,
                "expected_priority": row.get("expected_priority"),
                "predicted_priority": predictions_map[normalized],
                "expected_signals": row.get("expected_signals", []),
                "notes": row.get("notes", ""),
            }
        )

    if missing_accounts:
        raise RuntimeError(
            "Could not find these accounts in Snowflake ACCOUNT_SCORES: "
            + ", ".join(missing_accounts)
        )

    with open(output_path, "w", encoding="utf-8") as f:
        for item in output_rows:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"Wrote {len(output_rows)} predictions to {output_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="evals/labelled_accounts_template.jsonl")
    ap.add_argument("--output", default="evals/predictions.jsonl")
    args = ap.parse_args()

    try:
        write_predictions(args.input, args.output)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
