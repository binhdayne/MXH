"""Collect a bounded, versioned Wikipedia text corpus for enrichment.

Only relevant paragraphs are retained; source revision and HTML hash are kept.
"""
import argparse,hashlib,json,re
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import quote

ROOT=Path(__file__).parent
PAGES=['Adolf_Hitler','Winston_Churchill','Joseph_Stalin','Franklin_D._Roosevelt']
class Paragraphs(HTMLParser):
 def __init__(self):
  super().__init__();self.paragraphs=[];self.parts=None;self.skip=0
 def handle_starttag(self,tag,attrs):
  if tag in ('script','style','sup'):self.skip+=1
  if tag=='p':self.parts=[]
 def handle_endtag(self,tag):
  if tag=='p' and self.parts is not None:
   self.paragraphs.append(' '.join(''.join(self.parts).split()));self.parts=None
  if tag in ('script','style','sup'):self.skip=max(0,self.skip-1)
 def handle_data(self,text):
  if self.parts is not None and not self.skip:self.parts.append(text)
def collect(title,raw):
 parser=Paragraphs();parser.feed(raw.decode('utf8'))
 revision=re.search(rb'(?:/revision/|"wgRevisionId":\s*)(\d+)',raw)
 url='https://en.wikipedia.org/wiki/'+('Special:PermanentLink/'+revision[1].decode() if revision else quote(title))
 selected=[p for p in parser.paragraphs if len(p)>80 and re.search(r'\b194[0-5]\b|\b1939\b',p)
  and re.search(r'invas|declared war|pact|support|aid|conference|Churchill|Stalin|Roosevelt',p,re.I)]
 return [dict(id=f'{title}:{i}',title=title,url=url,sha256_html=hashlib.sha256(raw).hexdigest(),text=p,
  split='development' if title in PAGES[:2] else 'held_out') for i,p in enumerate(selected[:6])]
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--cache',type=Path);args=parser.parse_args()
 output=[]
 for title in PAGES:
  cached=args.cache/f'{title}.html' if args.cache else None
  if cached and cached.exists():raw=cached.read_bytes()
  else:
   request=Request('https://en.wikipedia.org/wiki/'+quote(title),headers={'User-Agent':'WWIIEntityAtlas/1.0 (course research)'})
   with urlopen(request,timeout=45) as response:raw=response.read()
  output.extend(collect(title,raw))
 (ROOT/'corpus').mkdir(exist_ok=True)
 (ROOT/'corpus/paragraphs.jsonl').write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in output)+'\n',encoding='utf8')
 print(f'Collected {len(output)} paragraphs; held-out split is by article.')
