"""Executa cada modulo de testes em processo isolado para liberar caches de sprites."""
import json,os,re,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 env=os.environ.copy();env['SDL_VIDEODRIVER']='dummy';env['SDL_AUDIODRIVER']='dummy'
 records=[];start=time.monotonic();report=ROOT/'docs/validacao_main_por_modulo.json'
 files=sorted((ROOT/'tests').glob('test_*.py'))
 for index,path in enumerate(files,1):
  module='tests.'+path.stem;before=time.monotonic()
  try:
   r=subprocess.run([sys.executable,'-m','unittest',module,'-q'],cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
   output=r.stderr+r.stdout;count=re.search(r'Ran (\d+) tests?',output)
   rec=dict(modulo=module,exit_code=r.returncode,testes=int(count[1]) if count else 0,segundos=round(time.monotonic()-before,2))
   if r.returncode:rec['erro']=output[-10000:]
  except subprocess.TimeoutExpired:
   rec=dict(modulo=module,exit_code=124,testes=0,segundos=180,erro='Tempo limite por modulo excedido.')
  records.append(rec)
  report.write_text(json.dumps(dict(modulos=records,total_testes=sum(v['testes'] for v in records),falhas=sum(v['exit_code']!=0 for v in records),concluido=index==len(files),segundos=round(time.monotonic()-start,2)),ensure_ascii=False,indent=2),encoding='utf-8')
  print(f"{index}/{len(files)} {module}: {'OK' if rec['exit_code']==0 else 'FAIL'} ({rec['testes']} tests)",flush=True)
  if rec['exit_code']:print(rec.get('erro','')[-3500:],flush=True)
 return any(v['exit_code'] for v in records)
if __name__=='__main__':raise SystemExit(main())
