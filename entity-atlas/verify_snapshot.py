"""Check topology, stored counts and PageRank fixed-point residuals."""
from graph_core import GraphStore
from collections import Counter
g=GraphStore();d=g.data;n=len(g.nodes);assert n>=2000 and len(d['edges'])>=5000
assert len({e['id'] for e in d['edges']})==len(d['edges'])
assert len({e['relation'] for e in d['edges']})>=10
for e in d['edges']:
 assert e['source'] in g.nodes and e['target'] in g.nodes
 assert e.get('sign') in (-1,1,None)
assert sum(d['stats']['community_sizes'].values())==n
for attribute,positive in [('pagerank',False),('positive_pagerank',True)]:
 adj={i:set() for i in g.nodes}
 for e in d['edges']:
  if (not positive or e.get('sign')==1) and e['source']!=e['target']:
   adj[e['source']].add(e['target']);adj[e['target']].add(e['source'])
 ranks={i:g.nodes[i][attribute] for i in g.nodes}
 assert abs(sum(ranks.values())-1)<1e-8 and min(ranks.values())>=0
 dangling=sum(ranks[i] for i in ranks if not adj[i])
 error=max(abs(ranks[i]-((1-.85)/n+.85*dangling/n+.85*sum(ranks[j]/len(adj[j]) for j in adj[i]))) for i in ranks)
 assert error<1e-8,(attribute,error)
 print(attribute,'fixed-point residual',error)
 if not positive:assert all(g.nodes[i]['degree']==len(adj[i]) for i in ranks)
ids={x['name']:x['id'] for x in d['nodes']}
context=g.context(ids['Adolf Hitler'],ids['Joseph Stalin'])
assert len(context)==2 and context[0]['source']=='Adolf Hitler' and context[1]['source']=='Joseph Stalin'
print(n,'nodes,',len(d['edges']),'edges,',len({e['relation'] for e in d['edges']}),'relation types. Snapshot checks passed.')
