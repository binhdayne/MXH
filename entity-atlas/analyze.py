"""Compute exact network metrics and reproducible random-graph comparisons."""
import hashlib,json,statistics,sys
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/"vendor"))
import networkx as nx
root=Path(__file__).parent
data=json.loads((root/"dist/graph.json").read_text(encoding="utf8"))

def pagerank_power(g,alpha=.85,tol=1e-12,max_iter=1000):
 """Uniform teleportation and dangling redistribution, no SciPy dependency."""
 n=len(g)
 rank=dict.fromkeys(g,1/n)
 for _ in range(max_iter):
  dangling=sum(rank[v] for v in g if g.degree(v)==0)
  updated=dict.fromkeys(g,(1-alpha)/n+alpha*dangling/n)
  for v in g:
   if g.degree(v):
    share=alpha*rank[v]/g.degree(v)
    for w in g[v]: updated[w]+=share
  if sum(abs(updated[v]-rank[v]) for v in g)<n*tol:
   return updated
  rank=updated
 raise RuntimeError("PageRank did not converge")
graph=nx.Graph()
graph.add_nodes_from(sorted(n["id"] for n in data["nodes"]))
graph.add_edges_from(sorted({tuple(sorted((e["source"],e["target"]))) for e in data["edges"] if e["source"]!=e["target"]}))
components=sorted(nx.connected_components(graph),key=len,reverse=True)
largest=graph.subgraph(components[0]).copy()
signature=hashlib.sha256(json.dumps({'nodes':sorted(largest),'edges':sorted(tuple(sorted(e)) for e in largest.edges())},sort_keys=True).encode()).hexdigest()
cache_path=root/'analysis_lcc_cache.json'
cache=json.loads(cache_path.read_text()) if cache_path.exists() else {}
cache_valid=cache.get('metric_version')==2 and cache.get('lcc_signature')==signature and cache.get('networkx')==nx.__version__ and '--recompute' not in sys.argv
def distances(g):
 total=pairs=0; diameter=0
 for a,dist in nx.all_pairs_shortest_path_length(g):
  total+=sum(dist.values());pairs+=len(dist)-1
  diameter=max(diameter,max(dist.values()))
 return total/pairs if pairs else 0,diameter,pairs//2
length,diameter,pairs=distances(largest)
print("Exact distances done",flush=True)
reachable_total=0;reachable_pairs=0
for comp in components:
 g=graph.subgraph(comp)
 if len(g)>1:
  l,d,p=distances(g) if len(g)!=len(largest) else (length,diameter,pairs)
  reachable_total+=l*p;reachable_pairs+=p
pagerank=pagerank_power(graph)
communities=nx.community.louvain_communities(graph,seed=1945)
membership={n:i for i,c in enumerate(sorted(communities,key=lambda c:(-len(c),min(c)))) for n in c}
core=nx.core_number(graph)
positive=nx.Graph();positive.add_nodes_from(graph)
positive.add_edges_from(sorted({tuple(sorted((e["source"],e["target"]))) for e in data["edges"] if e.get("sign")==1 and e['source']!=e['target']}))
positive_rank=pagerank_power(positive)
for n in data["nodes"]:
 n.update(degree=graph.degree(n["id"]),pagerank=pagerank[n["id"]],positive_pagerank=positive_rank[n["id"]],community=membership[n["id"]],core=core[n["id"]])
clustering=nx.average_clustering(largest)
baselines=cache['baselines'] if cache_valid else []
for seed in (() if cache_valid else (41,42,43)):
 reference=nx.gnm_random_graph(len(largest),largest.number_of_edges(),seed=seed)
 ref=reference.subgraph(max(nx.connected_components(reference),key=len)).copy()
 ref_length,_,_=distances(ref)
 baselines.append({"seed":seed,"nodes":len(ref),"clustering":nx.average_clustering(ref),"path_length":ref_length})
 print("Baseline",seed,flush=True)
cr=statistics.mean(x["clustering"] for x in baselines);lr=statistics.mean(x["path_length"] for x in baselines)
sigma=(clustering/cr)/(length/lr) if cr and length else None
degree_baselines=cache['degree_baselines'] if cache_valid else []
for seed in (() if cache_valid else (1941,1942,1943)):
 reference=largest.copy()
 swaps=nx.connected_double_edge_swap(reference,nswap=5*reference.number_of_edges(),seed=seed)
 ref_length,_,_=distances(reference)
 degree_baselines.append({'seed':seed,'nodes':len(reference),'successful_swaps':swaps,
  'clustering':nx.average_clustering(reference),'path_length':ref_length})
 print('Degree-preserving baseline',seed,flush=True)
cd=statistics.mean(x['clustering'] for x in degree_baselines)
ld=statistics.mean(x['path_length'] for x in degree_baselines)
stats={"nodes":len(graph),"edges":len(data["edges"]),"simple_edges":graph.number_of_edges(),"components":len(components),
 "largest_component":len(largest),"average_shortest_path_lcc":length,"diameter_lcc":diameter,"clustering_lcc":clustering,
 "reachable_pairs":reachable_pairs,"reachable_pair_mean":reachable_total/reachable_pairs,
 "reachable_fraction":reachable_pairs/(len(graph)*(len(graph)-1)/2),"global_distance":"undefined_disconnected",
 "communities":len(communities),"modularity":nx.community.modularity(graph,communities),
 "baselines":baselines,"sigma_er":sigma,
 "degree_baselines":degree_baselines,"sigma_degree":(clustering/cd)/(length/ld) if cd else None,
 "lcc_signature":signature,"baseline_cache_used":cache_valid,"networkx":nx.__version__,"metric_version":2,
 "projection":"Undirected unweighted simple graph, all relation types. Positive PageRank uses sign=+1 only.",
 "random_comparison":"3 G(n,m) LCC references plus 3 connected, degree-preserving rewired LCC references. Rewired controls request 5*m swaps; accepted swaps reported. Exploratory, not a calibrated significance test.",
 "method_counts":dict(Counter(e.get("method","unknown") for e in data["edges"])),
 "community_sizes":dict(Counter(membership.values()))}
data["stats"]=stats
(root/"dist/graph.json").write_text(json.dumps(data,ensure_ascii=False),encoding="utf8")
(root/"analysis.json").write_text(json.dumps(stats,indent=2),encoding="utf8")
cache_path.write_text(json.dumps({k:stats[k] for k in ('lcc_signature','networkx','metric_version','baselines','degree_baselines')},indent=2),encoding='utf8')
print(json.dumps(stats,indent=2))
