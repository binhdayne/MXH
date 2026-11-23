"""Record an actual multi-hop model response, never a fabricated example."""
import json,time
from pathlib import Path
from urllib.request import Request,urlopen
from graph_core import GraphStore
root=Path(__file__).parent;g=GraphStore();ids={n['name']:n['id'] for n in g.data['nodes']}
question='Hitler và Stalin có mối liên hệ gì qua đường đi được cung cấp? Giữ đúng năm và nêu giới hạn suy luận.'
payload={'start':ids['Adolf Hitler'],'target':ids['Joseph Stalin'],'question':question}
started=time.time()
req=Request('http://127.0.0.1:8765/api/answer',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
with urlopen(req,timeout=660) as response:result=json.load(response)
result.update(question=question,elapsed_seconds=time.time()-started,independent_human_score=None)
(root/'evaluation/rag_run.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print('Recorded multi-hop response. Citation IDs valid:',result['citation_ids_valid'],flush=True)
