#!/usr/bin/env python3
"""Turn the Snowflake scorecard result into data.json for the leaderboard.

Usage:  python3 make_data.py raw.json

`raw.json` is whatever the sql_exec tool returned for query.sql — this script
accepts either the full tool envelope ({"result_set": {"data": [...],
"resultSetMetaData": {"rowType": [...]}}}) or a plain list of row-arrays /
row-objects. Columns expected (from query.sql):
  EMPLOYEE_NAME, TENURE_MO, BOOK, ACTIVE_ACCTS, ORDERS, SELF_SERVE_ORDERS, OA_ORDERS, SEGMENT
"""
import json, sys, datetime, os

HERE = os.path.dirname(os.path.abspath(__file__))

def load_rows(path):
    with open(path) as f:
        blob = json.load(f)
    # Unwrap common envelopes.
    if isinstance(blob, dict):
        rs = blob.get("result_set") or blob.get("resultSet") or blob
        data = rs.get("data")
        meta = (rs.get("resultSetMetaData") or {}).get("rowType") or []
        cols = [c["name"].upper() for c in meta] if meta else None
        if data is not None:
            if cols:
                return [dict(zip(cols, row)) for row in data]
            return [{k.upper(): v for k, v in row.items()} for row in data]
        blob = blob.get("rows") or blob
    # Plain list.
    if isinstance(blob, list):
        if blob and isinstance(blob[0], dict):
            return [{k.upper(): v for k, v in row.items()} for row in blob]
    raise SystemExit("Could not find rows in " + path)

def num(v):
    return float(v) if v not in (None, "") else 0.0

def load_excluded():
    """Names to keep off the board permanently (departed reps, etc.), lower-cased."""
    p = os.path.join(HERE, "excluded_reps.json")
    if not os.path.exists(p):
        return set()
    with open(p) as f:
        return {n.strip().lower() for n in json.load(f).get("names", [])}

def main(path):
    rows = load_rows(path)
    excluded = load_excluded()
    reps = []
    skipped = []
    for r in rows:
        if r["EMPLOYEE_NAME"].strip().lower() in excluded:
            skipped.append(r["EMPLOYEE_NAME"])
            continue
        orders = num(r["ORDERS"])
        if orders <= 0:
            continue
        ss = num(r["SELF_SERVE_ORDERS"]); oa = num(r["OA_ORDERS"])
        reps.append({
            "name": r["EMPLOYEE_NAME"],
            "orders": int(orders),
            "self_serve": round(ss / orders, 4),
            "oa": round(oa / orders, 4),
            "rep_entered": round(1 - (ss + oa) / orders, 4),
            "combined": round((ss + oa) / orders, 4),
            "seg": r.get("SEGMENT") or "Established",
        })
    reps.sort(key=lambda x: -x["combined"])
    for i, r in enumerate(reps, 1):
        r["rank"] = i
    est = [r for r in reps if r["seg"] == "Established"] or reps
    team = {
        "combined": round(sum(r["combined"] for r in est) / len(est) * 100),
        "self_serve": round(sum(r["self_serve"] for r in est) / len(est) * 100),
        "oa": round(sum(r["oa"] for r in est) / len(est) * 100),
        "reps": len(reps),
    }
    data = {
        "meta": {"window_label": "last 90 days",
                 "generated": datetime.date.today().isoformat(), "goal": 90},
        "team": team,
        "reps": reps,
    }
    with open("data.json", "w") as f:
        json.dump(data, f, indent=1)
    print(f"Wrote data.json — {len(reps)} reps; team combined {team['combined']}% "
          f"(self-serve {team['self_serve']}%, OA {team['oa']}%)")
    if skipped:
        print(f"Excluded {len(skipped)} rep(s) per excluded_reps.json: {', '.join(skipped)}")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "raw.json")
