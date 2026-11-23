"""Download official Windows x64 CPU runtime and Qwen 3B Q4_K_M weights.

No package is installed globally. Download size is approximately 2.13 GB.
"""
import hashlib,urllib.request,zipfile
from pathlib import Path
ROOT=Path(__file__).parent/'runtime'
FILES=[
 ('https://github.com/ggml-org/llama.cpp/releases/download/b12651/llama-b12651-bin-win-cpu-x64.zip','llama.zip','b2d794fa7587aba29f654d717ff9b73e31caeabf50a7766692903008bbe0855d'),
 ('https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf','qwen2.5-3b-instruct-q4_k_m.gguf','626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d')]
def digest(path):
 sha=hashlib.sha256()
 with path.open('rb') as stream:
  while chunk:=stream.read(1024*1024):sha.update(chunk)
 return sha.hexdigest()
if __name__=='__main__':
 ROOT.mkdir(exist_ok=True)
 for url,name,expected in FILES:
  target=ROOT/name
  if not target.exists():
   print('Downloading',name,flush=True)
   partial=target.with_suffix(target.suffix+'.part')
   expected_size=2104932768 if name.endswith('.gguf') else 25096571
   for attempt in range(4):
    offset=partial.stat().st_size if partial.exists() else 0
    if offset==expected_size:break
    headers={'Range':f'bytes={offset}-'} if offset else {}
    with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=90) as response:
     if offset and (response.status!=206 or not response.headers.get('Content-Range','').startswith(f'bytes {offset}-')):
      raise RuntimeError('Server did not honor range request.')
     with partial.open('ab' if offset else 'wb') as output:
      while chunk:=response.read(1024*1024):output.write(chunk)
   if partial.stat().st_size!=expected_size:raise RuntimeError('Incomplete download; run setup_model.py again to resume.')
   partial.replace(target)
  if digest(target)!=expected:raise RuntimeError('Checksum mismatch: '+name)
  print('SHA-256 verified',name,flush=True)
 with zipfile.ZipFile(ROOT/'llama.zip') as archive:archive.extractall(ROOT/'bin')
 print('Ready. Start with Start-App.ps1 or see README.')
