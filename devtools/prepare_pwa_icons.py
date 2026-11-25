"""Exporta ícones PWA a partir do retrato aprovado de Jaum, sem alterar a arte fonte."""
import hashlib,json
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
def prepare_icons(root=ROOT):
    source=root/"assets/portraits/source/framed/manel.png"
    folder=root/"web/icons";folder.mkdir(parents=True,exist_ok=True)
    portrait=Image.open(source).convert("RGBA")
    records={}
    for name,size,maskable in (("pwa-192.png",192,False),("pwa-512.png",512,False),
                              ("pwa-maskable-512.png",512,True),("apple-touch-icon.png",180,False)):
        icon=Image.new("RGBA",(size,size),(9,14,13,255))
        # O rosto e sua moldura cabem no círculo seguro de raio 40% na versão maskable.
        bounds=(round(size*.48),round(size*.62)) if maskable else (round(size*.68),round(size*.86))
        art=ImageOps.contain(portrait,bounds,Image.Resampling.LANCZOS)
        icon.alpha_composite(art,((size-art.width)//2,(size-art.height)//2))
        if not maskable:
            draw=ImageDraw.Draw(icon)
            inset=max(2,round(size*.025))
            draw.rounded_rectangle((inset,inset,size-inset-1,size-inset-1),
                radius=round(size*.08),outline=(190,153,88),width=max(1,round(size*.012)))
        target=folder/name;icon.convert("RGB").save(target,optimize=True)
        records[name]=dict(size=[size,size],maskable=maskable,sha256=hashlib.sha256(target.read_bytes()).hexdigest())
    (folder/"art_manifest.json").write_text(json.dumps(dict(
        source=source.relative_to(root).as_posix(),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        treatment="Exportação proporcional do retrato aprovado; fundo escuro e moldura dourada. Fonte preservada.",
        icons=records),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":prepare_icons()

