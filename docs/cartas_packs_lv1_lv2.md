# Cartas dos packs LV1 e LV2

Integração local de Cartas.zip. Os 20 tipos disponíveis têm uma arte base dourada e uma arte LV2 prateada, totalizando 40 PNGs RGBA.

## Origem e organização

| Grupo | Folha LV1 | Folha LV2 | Cartas |
|---|---|---|---|
| 1 | Cards pack 1 Lv 1.png | Cards pack 2 Lv 2.png | Lança Perfurante, Bola de Fogo, Poção de Cura, Surto de Energia, Poção Venenosa |
| 2 | Cards pack 2 Lv 1.png | Cards pack 1 Lv 2.png | Machado Quebra-Escudo, Amuleto Dissipador, Adaga Sangrenta, Máscara Ancestral, Machados Gêmeos |
| 3 | Cards pack 3 Lv 1.png | Cards pack 3 Lv 2.png | Esfera Protetora, Soco Simples, Investida, Aura Rubra, Poção Fragilizante |
| 4 | Cards pack 4 Lv 1.png | Cards pack 4 Lv 2.png | Poção Purificadora, Totem Protetor, Zarabatana Venenosa, Disparo de Arco, Esfera Escudo |

Os nomes dos packs 1 e 2 LV2 estão invertidos no ZIP. O mapeamento do importador segue a identidade de cada carta. Totem, Zarabatana e Esfera Escudo LV2 têm custo 2 impresso na folha, mas o custo 3 da definição atual é composto dinamicamente no losango.

- Artes LV1 em assets/cards/<id>.png.
- Artes LV2 em assets/cards/lv2/<id>.png.
- assets/cards/art_manifest.json registra folha, recorte, dimensões, contorno e centroide do custo, referência da descrição e SHA-256 do ZIP.
- As 20 imagens anteriores foram arquivadas localmente em _arquivos_antigos_para_deletar/cartas_antes_packs_lv1_lv2/. Essa pasta é ignorada pelo Git.
- As folhas externas originais foram preservadas.

## Renderização

AssetManager.get_card_image(nome, level=1, cost=None, description=None) mantém o carregamento por nome e aceita nível e valores da instância. O cache distingue nível, custo e descrição. CardView e MerchantWorkshopView encaminham os dados da cópia. Os slots de cópias da mochila e o cemitério usam CardView. A coleção e as ofertas de loja exibem LV1. O altar usa LV1 no Antes e LV2 no Depois.

with_player_rules recompõe o interior escuro detectado na própria arte e centraliza o número pelo centroide do contorno, mantendo a borda dourada ou prateada. Cada uma das 40 artes tem seu próprio contorno no manifesto. As dimensões e proporções originais dos recortes são preservadas. O texto ilustrado é preservado quando corresponde à descrição registrada. Se a descrição da instância mudar, o texto passa a ser composto na área de regras. with_rules permanece para artes de intenções e consumidores legados.

## Reproduzir os recortes

Execute a partir da raiz do projeto com as dependências de desenvolvimento instaladas.

```powershell
python -B devtools/prepare_player_card_packs.py --source "C:/Users/Gabriel/OneDrive/Imagens/SpritesJogo/Cartas.zip"
```

Use --output para preparar os recortes em uma pasta de conferência. O importador segmenta cada carta com folga lateral e remove o quadriculado conectado ao exterior, mantendo os contornos.

## Conferência

tests/test_player_card_art.py cobre os 40 arquivos, transparência, mapeamento invertido, composição do custo, cache por nível e encaminhamento dos dados reais da cópia. O piloto devtools/preview_roguelite.py --smoke usa saves temporários.

## Revisão do alinhamento dos custos

O importador detecta o componente escuro fechado de cada losango e calcula seu contorno convexo, que cobre o número impresso. O número dinâmico usa somente a área visível do glifo para a centralização. O manifesto está na versão 2.

A Aura Rubra LV1 usava o centro aproximado (59, 50), deslocado para a direita. O centro medido passou a (49, 48). Todas as outras artes LV1/LV2 também foram medidas individualmente. Os testes verificam os 40 contornos, preservação dos pixels externos, mudança do custo e a regressão específica da Aura Rubra.
