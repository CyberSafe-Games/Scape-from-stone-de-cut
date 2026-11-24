# Retratos dos personagens

> Referência vigente — auditoria de 23/11/2026. [Estado atual](estado_atual.md). Relatos de validações datadas abaixo representam somente aquela execução.

Os retratos personalizados da HUD ficam em `assets/portraits/source`.
O `manifest.json` registra os nomes originais dos retratos comuns vindos de
`inimigos.zip`. A correspondência e os recortes ficam em
`src/systems/character_portraits.py`.

Álvaro e Tex têm retratos próprios para cada fase. Zanzara usa a arte da
versão necromante com a moldura do protagonista.

Slime e Macaco Selvagem usam artes de retrato dedicadas. As imagens
são carregadas sob demanda e reutilizadas em cache.

## Padronização de 24/11/2026

Todos os comuns têm a moldura do protagonista composta em memória com o mesmo
padding e proporção de Zanzara. As onze faces fornecidas usam recortes que
preservam o rosto; Viniurgo reutiliza seu conteúdo sem repetir a borda.
A moldura comum foi preservada; a auditoria abaixo atualiza as fontes e o enquadramento.
A HUD recebe uma imagem completa em contain; hud_portrait.png foi aposentado
e arquivado fora das pastas ativas. Fontes dos retratos não foram removidas.
Testes verificam bordas pixel-idênticas nos 14 tipos e cache em tamanhos reais.

## Auditoria de enquadramento — 24/11/2026

O preenchimento por cover e o crop percentual único foram substituídos nos
comuns por framed-contain com margem interna. Zanzara e os chefes preservam
seus retratos aprovados. Todas as fontes comuns são artes de retrato dedicadas;
nenhuma depende da animação/spritesheet. A moldura dourada permanece intacta.

| Inimigo | Tratamento |
|---|---|
| Slime | Novo retrato dedicado, corpo gelatinoso inteiro e proporção baixa natural. |
| Macaco Selvagem | Novo busto dedicado com cabeça, orelhas e ombros legíveis. |
| Viniurgo | Conteúdo do retrato original, sem borda dupla, contain e margem. |
| Guerreiro da Mata | Recorte individual e contain, preservando cabelo e rosto. |
| Golem das Ruínas | Recorte individual e contain, cabeça e placas inteiras. |
| Lagarto Couraçado | Recorte individual e contain, crista e focinho preservados. |
| Putrefato do Pântano | Recorte individual e contain, tentáculos e boca preservados. |
| Crocodilo Abissal | Recorte individual e contain, mandíbula/focinho completos. |
| Esqueleto Saqueador | Recorte individual e contain, crânio e ombros. |
| Morcego Sombrio | Recorte individual e contain, orelhas e asas presentes na fonte. |
| Centauro Vigia | Recorte individual e contain, cabelo, rosto e aljava. |
| Lutador Mascarado | Recorte individual e contain, capuz e máscara completos. |
| Vinimuth | Recorte individual e contain, cabelo e orelhas preservados. |
| Mago do Santuário | Recorte individual e contain, capuz e cajado preservados. |

Novas artes: assets/portraits/source/dedicated/slime.png e
assets/portraits/source/dedicated/macaco_selvagem.png. Prompts e SHA-256 em
[manifesto dos retratos dedicados](../assets/portraits/source/dedicated/art_manifest.json).
Não há PNG de retrato antigo de Slime/Macaco para arquivar; sprites e fontes
existentes continuam referenciados pelo jogo. As imagens de combate não foram
removidas para corrigir a HUD.

### Gerador comum legado

Além dos 14 tipos dos biomas, ENEMY_TYPES ainda registra Goblin e Guarda Sombrio.
Ambos receberam PNGs dedicados em dedicated/goblin.png e
dedicated/guarda_sombrio.png, com framed-contain. A cobertura total desta revisão
é de 16 tipos comuns. Chefes e minibosses não tiveram suas artes alteradas.
Os quatro prompts completos e hashes estão no manifesto da pasta dedicated/.
