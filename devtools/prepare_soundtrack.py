"""Prepara derivados OGG de trilha sem alterar os originais externos."""
from pathlib import Path
import hashlib,json,re,subprocess,sys
import imageio_ffmpeg
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(r'C:\Users\marco\Documents\Codex\2026-11-10\navegador-plugin-browser-openai-bundled-x20-2\outputs\trilha-sonora')
RECIPES=[('335081','menu_floresta_v1'),('190499','combate_tambores_v1'),('345242','chefes_selva_v1'),('262597','zanzara_ritual_v1'),('517862','zanzara_ancestrais_v1')]
ROUNDS={1:RECIPES,2:[('192142','chefes_jungle_tribe_v2'),('596656','chefes_jungle_chase_v2')]}
def main():
 rodada=int(sys.argv[1]) if len(sys.argv)>1 else 1
 recipes=ROUNDS[rodada]
 manifest=json.loads((SOURCE/f'fontes-rodada-{rodada}.json').read_text(encoding='utf-8-sig'))
 target=ROOT/'assets/audio/music';target.mkdir(parents=True,exist_ok=True)
 report=ROOT/f'docs/trilha_sonora_fontes_v{rodada}.json'
 for path in [report]+[target/(name+'.ogg') for _,name in recipes]:
  if path.exists():raise FileExistsError(path)
 ff=imageio_ffmpeg.get_ffmpeg_exe();records=[]
 for ident,name in recipes:
  entry=next(e for e in manifest['faixas'] if ident in e['nome_local']);src=SOURCE/'originais'/entry['nome_local']
  assert hashlib.sha256(src.read_bytes()).hexdigest()==entry['sha256']
  measure=subprocess.run([ff,'-hide_banner','-i',str(src),'-af','volumedetect','-f','null','-'],capture_output=True,text=True,errors='replace',check=True)
  mean=float(re.search(r'mean_volume: ([-\d.]+) dB',measure.stderr)[1]);peak=float(re.search(r'max_volume: ([-\d.]+) dB',measure.stderr)[1])
  gain=min(0,-24-mean,-12-peak);duration=entry['duracao_segundos']
  filters=f'volume={gain}dB,afade=t=in:d=0.35,afade=t=out:st={duration-.65}:d=0.65'
  dest=target/(name+'.ogg')
  subprocess.run([ff,'-nostdin','-v','error','-n','-i',str(src),'-af',filters,'-ar','44100','-ac','2','-c:a','libvorbis','-q:a','5',str(dest)],check=True)
  assert hashlib.sha256(src.read_bytes()).hexdigest()==entry['sha256']
  records.append(dict(arquivo=str(dest.relative_to(ROOT)),fonte=entry,filtros=filters,ganho_db=gain,media_origem_dbfs=mean,pico_origem_dbfs=peak,sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),loop_aprovado=False))
  print('Preparada:',dest.name,flush=True)
 report.write_text(json.dumps(dict(status='Piloto provisório; músicas e loops aguardam aprovação auditiva.',escuta_critica=False,volume_musica_piloto=.45,recursos=records),ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':main()
