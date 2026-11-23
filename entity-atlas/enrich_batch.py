"""Run the selected SLM on the versioned corpus and retain all proposals."""
import argparse,json,time
from pathlib import Path
from urllib.request import Request,urlopen
ROOT=Path(__file__).parent
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--limit',type=int,default=3)
 parser.add_argument('--split',choices=['development','held_out'],default='development')
 parser.add_argument('--paragraph-id')
 args=parser.parse_args()
 corpus=[json.loads(line) for line in (ROOT/'corpus/paragraphs.jsonl').read_text(encoding='utf8').splitlines()]
 output=ROOT/'evaluation'/f'qwen_{args.split}.jsonl';output.parent.mkdir(exist_ok=True)
 with output.open('w',encoding='utf8') as stream:
  for paragraph in [p for p in corpus if p['split']==args.split and (not args.paragraph_id or p['id']==args.paragraph_id)][:args.limit]:
   started=time.time()
   req=Request('http://127.0.0.1:8765/api/enrich',data=json.dumps({'text':paragraph['text'],'url':paragraph['url']}).encode(),headers={'Content-Type':'application/json'})
   with urlopen(req,timeout=660) as response:result=json.load(response)
   stream.write(json.dumps({'paragraph_id':paragraph['id'],'source_url':paragraph['url'],'elapsed_seconds':time.time()-started,**result},ensure_ascii=False)+'\n');stream.flush()
   print(paragraph['id'],len(result['validated_proposals']),'proposals',flush=True)
