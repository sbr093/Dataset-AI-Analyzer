import os
import tempfile
import csv
from app.agents.tools import summarize_dataset_tool, generate_chart_tool, detect_anomalies_tool
from app.agents.validation import validate_dataset_summary, validate_chart, validate_anomalies


def create_sample_csv(path):
    rows = [
        ["id", "region", "sales"],
        [1, "A", 100],
        [2, "B", 200],
        [3, "A", 150],
        [4, "C", 1000],  # outlier
    ]
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def test_summarize_and_chart_and_anomalies():
    tmpdir = tempfile.mkdtemp()
    csv_path = os.path.join(tmpdir, "sample.csv")
    create_sample_csv(csv_path)

    summary = summarize_dataset_tool(csv_path)
    assert validate_dataset_summary(summary), f"Invalid summary: {summary}"

    chart = generate_chart_tool(csv_path, x_axis="region", y_axis="sales")
    assert validate_chart(chart), f"Invalid chart: {chart}"

    anomalies = detect_anomalies_tool(csv_path)
    assert validate_anomalies(anomalies), f"Invalid anomalies: {anomalies}"
