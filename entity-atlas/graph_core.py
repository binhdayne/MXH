"""Evidence-preserving graph retrieval and validation of enrichment proposals."""
import json,re
from collections import deque
from pathlib import Path

ROOT=Path(__file__).parent
ENTITY_TYPES={"Person","Party","Government","Event"}
RELATIONS={
 "ATTENDED":None,"SIGNED":None,"REPRESENTED":None,"LED_GOVERNMENT":None,
 "LED_PARTY":None,"MILITARY_PACT":1,"NON_AGGRESSION_PACT":1,
 "INVADED":-1,"ORDERED_INVASION_OF":-1,"DECLARED_WAR_ON":-1,
 "JOINT_DECLARATION":1,"NOMINATES_CANDIDATE":1,"ELECTORAL_RIVAL":-1,
 "LEAVES_PARTY":-1,"JOINS_PARTY_AFTER_SWITCH":1,"DEMANDS_SURRENDER":-1,
 "DIRECTED_AID_TO":1,"CALLED_FOR_RESISTANCE_AGAINST":-1,"EXPRESSED_SUPPORT_FOR":1,
}
DOMAIN_RANGE={
 'ATTENDED':({'Person'},{'Event'}),'SIGNED':({'Person','Government'},{'Event'}),
 'REPRESENTED':({'Person'},{'Government'}),'LED_GOVERNMENT':({'Person'},{'Government'}),
 'LED_PARTY':({'Person'},{'Party'}),'MILITARY_PACT':({'Government'},{'Government'}),
 'NON_AGGRESSION_PACT':({'Government'},{'Government'}),'INVADED':({'Government'},{'Government'}),
 'ORDERED_INVASION_OF':({'Person'},{'Government'}),'DECLARED_WAR_ON':({'Person','Government'},{'Government'}),
 'NOMINATES_CANDIDATE':({'Party'},{'Person'}),'ELECTORAL_RIVAL':({'Person'},{'Person'}),
 'LEAVES_PARTY':({'Person'},{'Party'}),'JOINS_PARTY_AFTER_SWITCH':({'Person'},{'Party'}),
 'DEMANDS_SURRENDER':({'Person','Government'},{'Government'}),
 'DIRECTED_AID_TO':({'Person','Government'},{'Government'}),
 'CALLED_FOR_RESISTANCE_AGAINST':({'Person','Government'},{'Government'}),
}

class GraphStore:
 def __init__(self,path=None):
  self.data=json.loads(Path(path or ROOT/'dist/graph.json').read_text(encoding='utf8'))
  self.nodes={n['id']:n for n in self.data['nodes']}
  self.adj={i:[] for i in self.nodes}
  for e in self.data['edges']:
   self.adj[e['source']].append(e)
   if e['target']!=e['source']:self.adj[e['target']].append(e)

 def path(self,start,target,max_hops=4):
  if start not in self.nodes or target not in self.nodes:raise ValueError('Không tìm thấy thực thể.')
  previous={start:None};queue=deque([(start,0)])
  while queue:
   current,depth=queue.popleft()
   if current==target:break
   if depth>=max_hops:continue
   for edge in self.adj[current]:
    other=edge['target'] if edge['source']==current else edge['source']
    if other not in previous:
     previous[other]=(current,edge);queue.append((other,depth+1))
  if target not in previous:return None
  result=[];current=target
  while current!=start:
   current,edge=previous[current];result.append(edge)
  return list(reversed(result))

 def context(self,start,target):
  path=self.path(start,target)
  if path is None:raise ValueError('Không có đường đi trong 4 bước. Không đủ bằng chứng để trả lời.')
  if not path:raise ValueError('Hãy chọn hai thực thể khác nhau.')
  return [dict(citation=i+1,source=self.nodes[e['source']]['name'],
    target=self.nodes[e['target']]['name'],relation=e['relation'],year=e.get('year'),
    start_year=e.get('start_year'),end_year=e.get('end_year'),start_date=e.get('start_date'),end_date=e.get('end_date'),
    sign=e.get('sign'),url=e.get('wiki_url'),evidence=e.get('evidence'),event=e.get('event'),edge_id=e['id'])
    for i,e in enumerate(path)]

def validate_proposal(proposal,text):
 """No automatic acceptance: exact source spans plus a constrained ontology."""
 if not isinstance(proposal,dict):raise ValueError('Model output is not a JSON object.')
 entities=proposal.get('entities',[]);relations=proposal.get('relations',[])
 if not isinstance(entities,list) or not isinstance(relations,list):raise ValueError('Invalid entities/relations lists.')
 accepted=[];rejected=[];names=set();entity_types={}
 for entity in entities:
  if isinstance(entity,dict) and isinstance(entity.get('name'),str) and entity.get('type') in ENTITY_TYPES:
   names.add(entity['name'])
   entity_types[entity['name']]=entity['type']
 for relation in relations:
  reason=None
  if not isinstance(relation,dict):reason='invalid_object'
  elif relation.get('type') not in RELATIONS:reason='unknown_relation'
  elif relation.get('source') not in names or relation.get('target') not in names:reason='missing_entity'
  elif relation['type'] in DOMAIN_RANGE and (entity_types[relation['source']] not in DOMAIN_RANGE[relation['type']][0] or entity_types[relation['target']] not in DOMAIN_RANGE[relation['type']][1]):reason='domain_range_mismatch'
  elif not isinstance(relation.get('evidence'),str) or len(relation['evidence'])<8 or relation['evidence'] not in text:reason='evidence_not_verbatim'
  elif type(relation.get('sign')) not in (int,type(None)) or relation.get('sign')!=RELATIONS[relation['type']]:reason='sign_mismatch'
  elif relation.get('year') is not None and (type(relation['year']) is not int or not 1939<=relation['year']<=1945):reason='outside_scope_year'
  if reason:rejected.append({'proposal':relation,'reason':reason})
  else:accepted.append(relation)
 return {'entities':[e for e in entities if isinstance(e,dict) and e.get('name') in names],
   'validated_proposals':accepted,'rejected':rejected,'uncertain':proposal.get('uncertain',[]),
   'review_required':True,'note':'Validation checks structure and quoted spans. Human review must establish semantic correctness.'}

def check_generation(content,context):
 """Conservative development guards, not a semantic-accuracy certificate."""
 cited={int(x) for x in re.findall(r'\[(\d+)\]',content)}
 valid={e['citation'] for e in context};flags=[]
 if not cited or not cited<=valid:flags.append('missing_or_invalid_citation_ids')
 if cited&valid!=valid:flags.append('incomplete_path_citations')
 if re.search(r'[\u3400-\u9fff]',content):flags.append('unexpected_script_for_vietnamese_output')
 if re.search(r'dẫn đến|gây ra|caused|led to',content,re.I):flags.append('causal_language_without_causal_relation')
 return {'citation_ids_valid':bool(cited) and cited<=valid,
  'citation_coverage':len(cited&valid)/len(valid) if valid else 0,'verification_flags':flags,'generation_accepted':not flags}

def retrieval_fallback(context):
 lines=['Bản diễn giải của mô hình chưa qua bước kiểm tra. Bằng chứng truy xuất:']
 for e in context:
  period=f"{e['start_year']}–{e['end_year']}" if e.get('start_year') is not None else e.get('year')
  lines.append(f"[{e['citation']}] {e['source']} — {e['relation']} → {e['target']} ({period}).")
 lines.append('Đường đi thể hiện liên hệ trong dữ liệu; chưa chứng minh liên minh hoặc quan hệ nhân quả giữa hai đầu mút.')
 return '\n'.join(lines)
