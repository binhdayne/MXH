"""Apply explicitly reviewed existing-node relations to the project Neo4j graph.

python apply_reviewed.py evaluation/reviewed.json
The review file names both endpoint element IDs. No name-only entity merges.
"""
import argparse,json
from pathlib import Path
from urllib.request import Request,urlopen
from graph_core import GraphStore,RELATIONS

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('review_file');args=parser.parse_args()
 records=json.loads(Path(args.review_file).read_text(encoding='utf8'));graph=GraphStore();statements=[]
 for r in records:
  if r.get('approved') is not True or not r.get('reviewer'):raise ValueError('Every row must name a reviewer and approved=true.')
  if r['source_id'] not in graph.nodes or r['target_id'] not in graph.nodes:raise ValueError('Unknown endpoint ID.')
  relation=r['relation']
  if relation not in RELATIONS or r.get('sign')!=RELATIONS[relation]:raise ValueError('Invalid relation/sign.')
  if not r.get('evidence') or not r.get('wiki_url','').startswith('https://en.wikipedia.org/'):raise ValueError('Missing evidence/source.')
  if r.get('year') is not None and not 1939<=r['year']<=1945:raise ValueError('Year outside scope.')
  period={k:r[k] for k in ('start_year','end_year','start_date','end_date','year_semantics','section','locator','wiki_revision','source_checked_at') if k in r}
  if 'start_year' in period or 'end_year' in period:
   if not all(isinstance(period.get(k),int) for k in ('start_year','end_year')) or period['start_year']>period['end_year']:raise ValueError('Invalid relation period.')
   if period['end_year']<1939 or period['start_year']>1945:raise ValueError('Relation period outside study scope.')
  statements.append({'statement':f'''MATCH (a:WWII),(b:WWII) WHERE elementId(a)=$a AND elementId(b)=$b
   MERGE (a)-[r:{relation} {{atlas_key:$key}}]->(b)
   SET r.year=$year,r.sign=$sign,r.evidence=$evidence,r.wiki_url=$url,r.method=$method,
       r.reviewer=$reviewer,r.human_review_pending=$human_review_pending,r.review_status=$review_status
   SET r += $period
   RETURN count(r) AS written''',
   'parameters':{'a':r['source_id'],'b':r['target_id'],'key':r['key'],'year':r.get('year'),'sign':r.get('sign'),
    'evidence':r['evidence'],'url':r['wiki_url'],'reviewer':r['reviewer'],'human_review_pending':r.get('human_review_pending',True),
    'method':r.get('method','reviewed_text'),'review_status':r.get('review_status','reviewed'),'period':period}})
 request=Request('http://127.0.0.1:17474/db/neo4j/tx/commit',data=json.dumps({'statements':statements}).encode(),headers={'Content-Type':'application/json'})
 with urlopen(request,timeout=30) as response:result=json.load(response)
 if result['errors']:raise RuntimeError(result['errors'])
 if any(x['data'][0]['row'][0]!=1 for x in result['results']):raise RuntimeError('One or more endpoints did not match.')
 print('Applied',len(records),'reviewed relations. Run export_graph.py then analyze.py.')
