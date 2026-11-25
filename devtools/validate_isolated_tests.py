"""Executa cada modulo de testes em processo isolado para liberar caches de sprites."""
import argparse,json,os,re,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8',errors='replace')
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--report',default='docs/validacao_main_por_modulo.json')
 parser.add_argument('--resume',action='store_true',help='Preserva módulos já aprovados no relatório.')
 parser.add_argument('--recheck',nargs='*',default=[],help='Repete módulos específicos mesmo ao retomar.')
 args=parser.parse_args()
 env=os.environ.copy();env['SDL_VIDEODRIVER']='dummy';env['SDL_AUDIODRIVER']='dummy'
 records=[];start=time.monotonic();report=ROOT/args.report
 # Checkout limpo/CI não contém build/, que é ignorado pelo Git.
 report.parent.mkdir(parents=True,exist_ok=True)
 previous={r['modulo']:r for r in json.loads(report.read_text(encoding='utf-8'))['modulos']} if args.resume and report.exists() else {}
 files=sorted((ROOT/'tests').glob('test_*.py'))
 for index,path in enumerate(files,1):
  module='tests.'+path.stem;before=time.monotonic()
  if module in previous and previous[module]['exit_code']==0 and module not in args.recheck:
   records.append(previous[module]);continue
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
 report.write_text(json.dumps(dict(modulos=records,total_testes=sum(v['testes'] for v in records),falhas=sum(v['exit_code']!=0 for v in records),concluido=True,retomado=args.resume,segundos=round(time.monotonic()-start,2)),ensure_ascii=False,indent=2),encoding='utf-8')
 print(f"Concluído: {sum(v['testes'] for v in records)} testes, {sum(v['exit_code']!=0 for v in records)} módulos com falha.",flush=True)
 return any(v['exit_code'] for v in records)
if __name__=='__main__':raise SystemExit(main())
