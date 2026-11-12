"""Import the WWII CSV graph and diplomatic seed into Neo4j."""
import argparse
import base64
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from graph_io import read_rows, write_json

NODE_KINDS = {"WartimePolitician", "WartimeParty", "WartimeGovernment"}
PARTY_SWITCH = {"LEAVES_PARTY", "JOINS_PARTY_AFTER_SWITCH"}
RELATIONS = PARTY_SWITCH | {
    "ELECTORAL_RIVAL", "NOMINATES_CANDIDATE", "JOINT_DECLARATION",
    "DEMANDS_SURRENDER", "DIRECTED_AID_TO", "CALLED_FOR_RESISTANCE_AGAINST",
    "EXPRESSED_SUPPORT_FOR",
}
HISTORICAL_NAMES = {"Franklin D. Roosevelt", "Winston Churchill", "John Eric Loverseed"}


def query(url, statements, authorization=None):
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if authorization:
        headers["Authorization"] = authorization
    request = Request(url, data=json.dumps({"statements": statements}).encode(), headers=headers)
    try:
        with urlopen(request, timeout=90) as response:
            result = json.load(response)
    except HTTPError as error:
        raise RuntimeError(f"Neo4j HTTP {error.code}: {error.read().decode()[:1000]}") from error
    if result.get("errors"):
        raise RuntimeError(result["errors"])
    return result


def statement(cypher, **parameters):
    return {"statement": cypher, "parameters": parameters}


def group_nodes(rows):
    nodes = defaultdict(list)
    node_ids = set()
    named_nodes = set()
    for row in rows:
        label = row.pop("kind")
        node_id = row["id"]
        if label not in NODE_KINDS:
            raise ValueError(f"Unknown node label: {label!r}")
        if not node_id or node_id in node_ids:
            raise ValueError(f"Missing or duplicate node ID: {node_id!r}")
        if label == "WartimeGovernment" or (
            label == "WartimePolitician" and row["name"] in HISTORICAL_NAMES
        ):
            key = (label, row["name"])
            if key in named_nodes:
                raise ValueError(f"Duplicate seed identity: {key!r}")
            named_nodes.add(key)
        node_ids.add(node_id)
        nodes[label].append(row)
    return nodes, node_ids


def group_edges(rows, node_ids):
    edges = defaultdict(list)
    edge_ids = set()
    for row in rows:
        relation = row.pop("relation")
        edge_id = row["id"]
        if relation not in RELATIONS:
            raise ValueError(f"Unknown relationship type: {relation!r}")
        if not edge_id or edge_id in edge_ids:
            raise ValueError(f"Missing or duplicate edge ID: {edge_id!r}")
        if row["source"] not in node_ids or row["target"] not in node_ids:
            raise ValueError(f"Edge {edge_id!r} has an endpoint missing from nodes.csv")
        row["sign"] = int(row["sign"])
        row["year"] = int(row["year"])
        if row["sign"] not in {-1, 1} or row["symmetric"] not in {"True", "False"}:
            raise ValueError(f"Invalid sign or symmetry for edge {edge_id!r}")
        row["symmetric"] = row["symmetric"] == "True"
        row["category"] = ("switch" if relation in PARTY_SWITCH
                           else "support" if row["sign"] == 1 else "opposition")
        edge_ids.add(edge_id)
        edges[relation].append(row)
    return edges


def node_statements(nodes):
    for label, records in nodes.items():
        if label == "WartimeGovernment":
            named = records
            by_id = []
        elif label == "WartimePolitician":
            named = [row for row in records if row["name"] in HISTORICAL_NAMES]
            by_id = [row for row in records if row["name"] not in HISTORICAL_NAMES]
        else:
            named = []
            by_id = records
        if named:
            yield statement(
                f"UNWIND $rows AS row MERGE (n:WWII:{label} {{name: row.name}}) SET n += row",
                rows=named,
            )
        if by_id:
            yield statement(
                f"UNWIND $rows AS row MERGE (n:WWII:{label} {{id: row.id}}) SET n += row",
                rows=by_id,
            )


def import_statements(nodes, edges):
    seed = Path(__file__).with_name("diplomacy_seed.cypher").read_text(encoding="utf8")
    statements = [statement(cypher.strip()) for cypher in seed.split(";") if cypher.strip()]
    statements.extend(node_statements(nodes))
    for relation, records in edges.items():
        statements.append(statement(f"""
            UNWIND $rows AS row
            MATCH (a:WWII {{id: row.source}}), (b:WWII {{id: row.target}})
            MERGE (a)-[r:{relation} {{id: row.id}}]->(b)
            SET r += row
        """, rows=records))
    statements.append(statement("""
        MATCH (:WWII)-[r]->(:WWII) WHERE r.method IS NULL
        SET r.method = 'manual',
            r.category = CASE r.sign WHEN 1 THEN 'support' WHEN -1 THEN 'opposition' ELSE 'context' END
    """))
    return statements


def component_sizes(vertices, links):
    neighbors = defaultdict(set)
    for source, target, *_ in links:
        neighbors[source].add(target)
        neighbors[target].add(source)
    unseen = {node_id for node_id, _ in vertices}
    sizes = []
    while unseen:
        stack = [unseen.pop()]
        size = 0
        while stack:
            current = stack.pop()
            size += 1
            newly_seen = neighbors[current] & unseen
            unseen.difference_update(newly_seen)
            stack.extend(newly_seen)
        sizes.append(size)
    return sorted(sizes, reverse=True)


def summarize(vertices, links):
    sizes = component_sizes(vertices, links)
    return dict(
        nodes=len(vertices), edges=len(links),
        node_types=dict(Counter(v[1] for v in vertices)),
        edge_types=dict(Counter(e[2] for e in links)),
        methods=dict(Counter(e[4] for e in links)),
        signs=dict(Counter(str(e[3]) if e[3] is not None else "neutral" for e in links)),
        categories=dict(Counter(e[5] for e in links)),
        signed_types=len({e[2] for e in links if e[3] is not None}),
        components=len(sizes), largest_components=sizes[:5],
    )


def authorization_header():
    password = os.environ.get("NEO4J_PASSWORD")
    if not password:
        return None
    username = os.environ.get("NEO4J_USERNAME", "neo4j")
    encoded = base64.b64encode(f"{username}:{password}".encode()).decode("ascii")
    return f"Basic {encoded}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--http", default="http://127.0.0.1:17474")
    parser.add_argument("--database", default="neo4j")
    parser.add_argument("--data", type=Path, default=Path("data"))
    args = parser.parse_args()

    nodes, node_ids = group_nodes(read_rows(args.data / "nodes.csv"))
    edges = group_edges(read_rows(args.data / "edges.csv"), node_ids)
    endpoint = f"{args.http.rstrip('/')}/db/{args.database}/tx/commit"
    authorization = authorization_header()
    statements = import_statements(nodes, edges)
    statements.extend([
        statement("MATCH (n:WWII) RETURN elementId(n), head([l IN labels(n) WHERE l <> 'WWII'])"),
        statement("MATCH (a:WWII)-[r]->(b:WWII) RETURN elementId(a), elementId(b), type(r), r.sign, r.method, r.category"),
    ])
    results = query(endpoint, statements, authorization)["results"]
    vertices = [item["row"] for item in results[-2]["data"]]
    links = [item["row"] for item in results[-1]["data"]]
    expected = sum(map(len, edges.values()))
    observed = sum(edge[4] != "manual" for edge in links)
    if expected != observed:
        raise RuntimeError(f"Expected {expected} generated edges, found {observed}.")
    stats = summarize(vertices, links)
    write_json(args.data / "neo4j_stats.json", stats)
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
