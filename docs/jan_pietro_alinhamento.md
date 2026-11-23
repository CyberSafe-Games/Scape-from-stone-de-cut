# Jan-Pietro: estabilização de postura — 23/11/2026

Revisão motivada pelo vídeo de combate enviado pelo usuário. O preparo anterior
redimensionava separadamente cada pose de idle; o caminho de desenho ainda
realinhava a silhueta por quadro, usando inclusive armas/efeitos na estimativa.
A combinação produzia oscilação lateral e vertical.

## Apoio e reprodução

- Seis folhas RGBA 4×2, células de 448×320, total de 48 quadros.
- Extração continua da esquerda para a direita, de cima para baixo.
- Apoio das botas em **(224, 318)**; os dois pixels inferiores da célula ficam
  transparentes. O cálculo usa botas opacas, sem auras, adagas ou partículas.
- Todos os oito quadros do idle usam a mesma escala de preparo e exatamente os
  mesmos pixels nas botas. O registro do tronco compensa o deslocamento do rosto,
  diminuindo gradualmente a correção até zerá-la antes dos pés, sem zoom por quadro.
- Idle: **160 ms por pose (6,25 FPS)**. Ordem de inspiração/expiração
  0,2,4,6,7,5,3,1,3,5,7,6,4,2 (índices zero). Todos os oito desenhos são usados;
  essa ordem de reprodução não altera o fatiamento original.
- Dano, giro, estocada, regeneração e corte em X abrem e fecham com a mesma
  guarda do idle; as seis poses centrais continuam representando a ação.
- O renderizador não realinha novamente o idle/dano desse chefe. As folhas já
  estão voltadas para a esquerda, sem flip por quadro. Escala de exibição e
  deslocamento intencional dos ataques melee continuam no caminho existente.

## Reprodução e arquivo local

O preparador canônico aceita --boss Boss5 para atualizar somente Jan-Pietro.
Ele chama devtools/stabilize_jan_pietro.py depois da limpeza e paleta.
O manifesto em assets/bosses/sheets_eight/manifest.json registra os 48 apoios,
deslocamentos, caixas finais e centros do rosto antes/depois.

As seis folhas e a paleta anteriores foram preservadas em
_arquivos_antigos_para_deletar/jan_antes_realinhamento_2026-11-23/, junto da
cópia do manifesto anterior; a pasta permanece ignorada pelo Git. Os originais
externos, o reparo anatômico já aprovado e os outros dois chefes foram preservados.

## Validação

- 24 testes direcionados aprovados.
- Oito regressões novas em tests/test_jan_pietro_stance.py: 48 apoios, botas
  idênticas, oito desenhos distintos, cadência, transições e ausência de segundo
  alinhamento. O desenho real de EntityView.draw_enemy também é amostrado por
  três ciclos para comparar os pixels de apoio na arena.
- Relatório consolidado incremental: **698 testes em 73 módulos, zero falhas**;
  os módulos afetados foram reexecutados, os demais resultados foram preservados.
- Atlas estático inspecionado e comparação animada antes/depois exportada.
  Isso não substitui a avaliação perceptual do usuário durante a partida.
