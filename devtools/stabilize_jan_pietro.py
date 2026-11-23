"""Registro de postura de Jan-Pietro; sem redesenho, zoom por quadro ou IA.

Recebe os quadros já recortados/limpos do preparador canônico. A cópia da base
das botas no idle garante apoio idêntico, sem usar adagas/auras como pivô.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from PIL import Image

SIZE=(448,320)
ANCHOR=(224,318)
BOOT_TOP=292


def support_anchor(frame):
    a=np.array(frame).astype(int)
    r,g,b,alpha=a.transpose(2,0,1)
    yy,xx=np.indices(alpha.shape)
    warm=(r>b+3)&(r>g*.95)&(r<g*2.5)&(r<230)
    dark=(np.maximum.reduce((r,g,b))<65)&((np.maximum.reduce((r,g,b))-np.minimum.reduce((r,g,b)))<20)
    boots=((alpha>200)&(yy>=BOOT_TOP)&(warm|dark)&(xx>120)&(xx<325))
    y,x=np.where(boots)
    if len(x)<12:
        raise ValueError('Pés sem apoio opaco suficiente; revisar o recorte.')
    return ((int(x.min())+int(x.max())+1)//2,int(y.max())+1)


def head_center(frame):
    """Centro da pele do rosto, medido acima do tronco, sem incluir as adagas."""
    a=np.array(frame).astype(int)
    r,g,b,alpha=a.transpose(2,0,1)
    yy,xx=np.indices(alpha.shape)
    skin=((alpha>200)&(r>95)&(r>g*1.22)&(r<g*1.9)&(g>b*1.2)
          &(yy<225)&(yy>165)&(xx>185)&(xx<255))
    # O rosto do idle é o maior componente de pele nessa região.
    visited=np.zeros(skin.shape,dtype=bool)
    parts=[]
    for y,x in zip(*np.where(skin)):
        if visited[y,x]:continue
        queue=[(int(x),int(y))]
        points=[]
        while queue:
            px,py=queue.pop()
            if visited[py,px] or not skin[py,px]:continue
            visited[py,px]=True
            points.append((px,py))
            for nx,ny in ((px-1,py),(px+1,py),(px,py-1),(px,py+1)):
                if 0<=nx<SIZE[0] and 0<=ny<SIZE[1] and not visited[ny,nx]:queue.append((nx,ny))
        parts.append(points)
    if not parts or len(max(parts,key=len))<20:
        raise ValueError('Rosto do idle não identificado; revisar a referência.')
    points=max(parts,key=len)
    x,y=zip(*points)
    return ((min(x)+max(x))/2,(min(y)+max(y))/2)


def translate(frame,offset):
    out=Image.new('RGBA',SIZE)
    out.alpha_composite(frame,offset)
    return out


def register_idle(frame,target_head,breath):
    """Compensa deslocamento da pose; deslocamento se anula antes das botas.

    Cada linha preserva sua largura. O pequeno registro vertical se limita ao
    tronco; nenhuma escala independente é aplicada a um quadro.
    """
    cx,cy=head_center(frame)
    dx=target_head[0]-cx
    dy=target_head[1]+breath-cy
    source=np.array(frame)
    yy,xx=np.indices(source.shape[:2])
    t=np.clip((yy-230)/(BOOT_TOP-230),0,1)
    weight=1-t*t*(3-2*t)
    sample_x=np.rint(xx-dx*weight).astype(int)
    sample_y=np.rint(yy-dy*weight).astype(int)
    valid=(sample_x>=0)&(sample_x<SIZE[0])&(sample_y>=0)&(sample_y<SIZE[1])
    result=np.zeros_like(source)
    result[valid]=source[sample_y[valid],sample_x[valid]]
    return Image.fromarray(result)


def stabilize_rows(rows):
    if set(rows)!={'idle','dano','ultimate','atk1','healer2','atk3'}:
        raise ValueError('Jan-Pietro deve ter exatamente seis grupos de oito quadros.')
    audit={}
    for group,frames in rows.items():
        if len(frames)!=8:raise ValueError(f'{group}: esperados oito quadros.')
        records=[]
        for i,frame in enumerate(frames):
            before=support_anchor(frame)
            offset=(ANCHOR[0]-before[0],ANCHOR[1]-before[1])
            frames[i]=translate(frame,offset)
            for _ in range(3):
                actual=support_anchor(frames[i])
                if actual==ANCHOR:break
                correction=(ANCHOR[0]-actual[0],ANCHOR[1]-actual[1])
                frames[i]=translate(frames[i],correction)
                offset=(offset[0]+correction[0],offset[1]+correction[1])
            records.append({'frame':i+1,'before_anchor':list(before),'offset':list(offset),
                            'after_anchor':list(support_anchor(frames[i]))})
        audit[group]=records
    target=head_center(rows['idle'][0])
    feet=rows['idle'][0].crop((0,BOOT_TOP,SIZE[0],SIZE[1]))
    # Oito desenhos originais, compensados; uma respiração de somente um pixel.
    for i,frame in enumerate(rows['idle']):
        audit['idle'][i]['before_head']=list(head_center(frame))
        breath=(0,0,-1,-1,-1,-1,0,0)[i]
        for _ in range(4):
            frame=register_idle(frame,target,breath)
            current=head_center(frame)
            if abs(current[0]-target[0])<=1 and abs(current[1]-target[1]-breath)<=1:
                break
        frame.paste(feet,(0,BOOT_TOP))
        rows['idle'][i]=frame
        audit['idle'][i]['after_head']=list(head_center(frame))
    # A mesma pose de guarda abre e fecha as ações, evitando saltos de postura
    # na troca de estado. Preparação/impacto/recuperação centrais são preservados.
    ready=rows['idle'][0]
    for group,frames in rows.items():
        if group!='idle':
            frames[0]=ready.copy()
            frames[-1]=ready.copy()
    for group,frames in rows.items():
        for i,frame in enumerate(frames):
            if support_anchor(frame)!=ANCHOR:raise ValueError((group,i,support_anchor(frame)))
            # Mantém o respiro inferior da célula depois do deslocamento.
            # O contorno opaco das botas já termina antes dessa faixa.
            frame.paste((0,0,0,0),(0,ANCHOR[1],SIZE[0],SIZE[1]))
            if support_anchor(frame)!=ANCHOR:raise ValueError('Margem invadiu as botas.')
            audit[group][i]['after_anchor']=list(ANCHOR)
            audit[group][i]['after_bbox']=list(frame.getbbox())
    return rows,{'version':1,'anchor':list(ANCHOR),'boot_top':BOOT_TOP,
                 'runtime_alignment':False,'scale_per_frame':False,'idle_frame_ms':160,
                 'idle_order':[0, 2, 4, 6, 7, 5, 3, 1, 3, 5, 7, 6, 4, 2],'frames':audit}


def read_rows(folder):
    rows={}
    for group in ('idle','dano','ultimate','atk1','healer2','atk3'):
        with Image.open(folder/f'{group}.png') as sheet:
            rows[group]=[sheet.convert('RGBA').crop((col*448,row*320,(col+1)*448,(row+1)*320))
                         for row in range(2) for col in range(4)]
    return rows


def write_rows(rows,folder):
    folder.mkdir(parents=True,exist_ok=True)
    for group,frames in rows.items():
        sheet=Image.new('RGBA',(1792,640))
        for i,frame in enumerate(frames):sheet.alpha_composite(frame,((i%4)*448,(i//4)*320))
        sheet.save(folder/f'{group}.png',optimize=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    rows,audit=stabilize_rows(read_rows(args.source))
    write_rows(rows,args.output)
    (args.output/'alignment.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('48 quadros registrados em (224,318); botas do idle idênticas.')
