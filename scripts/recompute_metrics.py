# scripts/recompute_metrics.py

import os
import csv

from src.metrics import load_log, compute_basic_metrics, aggregate_by_condition

ROOT = os.path.dirname(os.path.dirname(__file__))
RAW_LOG_DIR = os.path.join(ROOT, "logs", "raw")
AGG_DIR = os.path.join(ROOT, "logs", "aggregated")


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def main():
    ensure_dir(AGG_DIR)

    run_metrics = {}

    # Scan all raw log files
    for fname in os.listdir(RAW_LOG_DIR):
        if not fname.endswith(".csv"):
            continue
        path = os.path.join(RAW_LOG_DIR, fname)
        rows = load_log(path)
        metrics = compute_basic_metrics(rows)

        run_id = os.path.splitext(fname)[0]  # e.g. "condition_A_seed_101"
        run_metrics[run_id] = metrics

    # Aggregate by condition (A/B/C/D)
    summary = aggregate_by_condition(run_metrics)

    # Write summary_by_condition.csv
    summary_path = os.path.join(AGG_DIR, "summary_by_condition.csv")
    with open(summary_path, "w", newline="") as f:
        fieldnames = ["condition", "success", "mean_risk", "max_risk", "steps"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for cond, m in summary.items():
            row = {"condition": cond}
            row.update(m)
            writer.writerow(row)

    print(f"[INFO] Wrote {summary_path}")


if __name__ == "__main__":
    main()