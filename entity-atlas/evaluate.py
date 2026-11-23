"""Strict NER/RE metrics on fully annotated held-out paragraphs.

python evaluate.py --gold evaluation/gold.jsonl --pred evaluation/qwen_held_out.jsonl
Unannotated template rows are rejected, never treated as negative examples.
"""
import argparse,json,math
from pathlib import Path

def rows(path):return [json.loads(x) for x in Path(path).read_text(encoding='utf8').splitlines() if x.strip()]
def scores(gold,pred):
 tp=len(gold&pred);fp=len(pred-gold);fn=len(gold-pred)
 p=tp/(tp+fp) if tp+fp else None;r=tp/(tp+fn) if tp+fn else None
 f=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None
 n=tp+fp;lower=None
 if n:
  z=1.96;rate=tp/n
  lower=(rate+z*z/(2*n)-z*math.sqrt(rate*(1-rate)/n+z*z/(4*n*n)))/(1+z*z/n)
 return dict(tp=tp,fp=fp,fn=fn,precision=p,recall=r,f1=f,precision_wilson_lower_95=lower)
def evaluate(gold,pred):
 lookup={r['paragraph_id']:r for r in pred}
 ge=set();pe=set();gr=set();pr=set();types=set()
 for row in gold:
  if row.get('annotated') is not True:raise ValueError('Unannotated gold row: '+row['paragraph_id'])
  key=row['paragraph_id'];p=lookup.get(key,{});raw=p.get('raw','{}')
  try:raw=json.loads(raw) if isinstance(raw,str) else raw
  except (ValueError,TypeError):raw={}
  for source,dest in [(row,ge),(raw,pe)]:
   for e in source.get('entities',[]):dest.add((key,e['name'],e['type']))
  for source,dest in [(row,gr),(raw,pr)]:
   for e in source.get('relations',[]):
    relation=e.get('type');types.add(relation)
    dest.add((key,e.get('source'),e.get('target'),relation,e.get('sign'),e.get('year')))
 return {'paragraphs':len(gold),'ner_exact':scores(ge,pe),'re_strict':scores(gr,pr),
  'per_relation':{str(t):scores({e for e in gr if e[3]==t},{e for e in pr if e[3]==t}) for t in sorted(types,key=str)},
  'scope':'Raw model proposals; exact entity names/types and exact relation endpoints/type/sign/year. Macro metrics are not inferred from table audit.'}
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--gold',required=True);parser.add_argument('--pred',required=True)
 parser.add_argument('--output',default='evaluation/held_out_metrics.json');args=parser.parse_args()
 result=evaluate(rows(args.gold),rows(args.pred));Path(args.output).write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result,indent=2))
