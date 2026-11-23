import json,time,sys
from pathlib import Path
from urllib.request import Request,urlopen
root=Path(__file__).parent
query="""MATCH (n:WWII) RETURN elementId(n) AS id, properties(n) AS properties, labels(n) AS labels"""
edges="""MATCH (a:WWII)-[r]->(b:WWII) RETURN elementId(r) AS id, elementId(a) AS source, elementId(b) AS target, type(r) AS relation, properties(r) AS properties"""
for attempt in range(25):
 try:
  req=Request("http://127.0.0.1:17474/db/neo4j/tx/commit",data=json.dumps({"statements":[{"statement":query},{"statement":edges}]}).encode(),headers={"Content-Type":"application/json"})
  with urlopen(req,timeout=20) as r: data=json.load(r)
  assert not data["errors"],data["errors"]
  break
 except Exception:
  if attempt==24:raise
  time.sleep(1)
def rows(result):return [dict(zip(result["columns"],item["row"])) for item in result["data"]]
nodes=[]
for row in rows(data["results"][0]):
 props=row["properties"]; nodes.append(dict(props,id=row["id"],kind=next(l for l in row["labels"] if l!="WWII")))
links=[]
for row in rows(data["results"][1]):
 props=row.pop("properties"); links.append(dict(props,**row))
(root/"dist/graph.json").write_text(json.dumps({"nodes":nodes,"edges":links},ensure_ascii=False),encoding="utf8")
print(len(nodes),len(links))
