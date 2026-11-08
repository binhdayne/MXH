"""Convert the portable CSVs to Neo4j admin-import CSVs."""
import argparse
import csv
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("data", type=Path)
parser.add_argument("destination", type=Path)
args = parser.parse_args()
args.destination.mkdir(parents=True, exist_ok=True)

for source_name, dest_name, special in [
    ("nodes.csv", "nodes.neo.csv", {"id": "id:ID(Entity)", "kind": ":LABEL"}),
    ("edges.csv", "edges.neo.csv", {
        "source": ":START_ID(Entity)", "target": ":END_ID(Entity)", "relation": ":TYPE",
        "sign": "sign:int", "symmetric": "symmetric:boolean", "revision": "revision:long",
    }),
]:
    with (args.data / source_name).open(encoding="utf8", newline="") as source:
        with (args.destination / dest_name).open("w", encoding="utf8", newline="") as destination:
            reader = csv.DictReader(source)
            writer = csv.writer(destination)
            writer.writerow([special.get(column, column) for column in reader.fieldnames])
            for record in reader:
                if source_name == "nodes.csv":
                    record["kind"] = "Entity;" + record["kind"]
                else:
                    record["symmetric"] = record["symmetric"].lower()
                writer.writerow([record[column] for column in reader.fieldnames])
