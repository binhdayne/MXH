"""Read and write the CSV and JSON files shared by the pipeline."""
import csv
import json


def read_rows(path):
    with path.open(encoding="utf8", newline="") as file:
        return list(csv.DictReader(file))


def write_rows(path, rows):
    with path.open("w", encoding="utf8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf8")
