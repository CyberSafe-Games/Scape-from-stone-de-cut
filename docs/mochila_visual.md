# Mochila Ancestral — mesa de expedição

> Referência vigente — auditoria de 23/11/2026. [Estado atual](estado_atual.md). Relatos de validações datadas abaixo representam somente aquela execução.

Redesign de 23/11/2026. Cenário de acampamento entre ruínas, bolsa aberta e
bancada de madeira; couro costurado, bronze/ouro envelhecido, verde-musgo e
luz âmbar. A composição reutiliza os componentes aprovados do Mercado Silencioso
e do Altar, sem mudar suas telas.

## Assets

- assets/ui/backpack/expedition_background.png: cenário ilustrado 16:9.
- assets/ui/backpack/leather_slot.png: compartimento de couro com centro e exterior transparentes.
- Moldura externa compartilhada: assets/ui/shop/offer_frame.png.

As duas imagens foram geradas com a ferramenta integrada image_gen e copiadas
para o projeto. Fontes/prompts e hashes em assets/ui/backpack/art_manifest.json.
A mochila anterior usava o fundo compartilhado do jogo e desenho por código;
nenhuma imagem exclusiva antiga foi substituída. O fundo compartilhado continua
ativo, portanto não há imagens obsoletas para mover nesta tarefa.

## Composição e interação

- Baralho à esquerda: dezoito espaços individuais, quantidade atual, mínimo de
  seis cartas e limite de três cópias por tipo. Espaços ocupados mostram a arte
  e o nível da cópia real; vazios têm número e identificação.
- Coleção ao centro: seis tipos por página e filtros combináveis por posse,
  tipo, custo real e nível. Os botões percorrem as opções; filtros ativos têm
  destaque. Resultado vazio mantém todos os controles acessíveis.
- Os filtros descrevem a **próxima cópia livre**, respeitando a prioridade LV2
  já existente no inventário. Quando todas estão equipadas, mostram a melhor
  cópia para consulta. Nenhum filtro promete equipar um nível diferente do que
  a lógica existente escolherá. Depois de equipar/retirar, filtros e página
  são recalculados.
- Clique numa carta da coleção adiciona uma cópia; clique no espaço remove
  aquela cópia. Os botões de esvaziar/sortear, confirmações, teclas e bloqueio
  de cartas indisponíveis continuam existentes.
- Inspeção fixa à direita: hover sobre cartas ou espaços mostra a própria carta
  completa; o painel não cria eventos, não cobre os botões e não muda o deck.
  Quando não há hover, exibe a carta selecionada.
- As artes LV1/LV2 e custo/descrição dinâmicos são compostos por get_card_image,
  usando o mesmo enquadramento com padding da Loja/Altar. Sem badge adicional.
- Ultimates mantêm aba própria, arte dourada integral, carga/custo e troca
  persistente. O texto informa corretamente carga zero ao iniciar cada combate.
- Equipar/retirar emite ui.confirm a 65% e feedback de brilho/partículas no
  espaço alterado. A troca de ultimate usa o mesmo feedback, sem sons novos.
- Regras de deck e save não foram alteradas; rascunho abaixo do mínimo nunca
  sobrescreve o último deck válido, inclusive ao fechar a janela.

## Código

BackpackScene conserva eventos/transações. BackpackView concentra ilustração,
composição, preview e feedback e reutiliza MerchantWorkshopView sem alterar
esse componente compartilhado. AssetManager carrega os novos arquivos pelo
carregador de imagens de serviço já existente.

## Validação

Testes novos em tests/test_backpack_visual.py: carta LV2/custo/descrição reais
no hover sem mutação, filtros e página vazia, posicionamento do preview fora dos
controles, persistência/reabertura, falha de gravação, baralho vazio/completo,
troca de ultimate, seleção correta do próximo nível e feedback no espaço certo.

83 testes direcionados aprovados. Smoke sem janelas de Loja, Altar, Mochila,
batalha, recompensas e preparação aprovado com saves temporários. O piloto
devtools/preview_roguelite.py --smoke --output <pasta> também exporta mochila,
hover LV2, ultimates e deck vazio, sem ler ou gravar saves reais.

Relatório completo: docs/validacao_mochila_visual.json.

Resultado consolidado: **712 testes em 75 módulos, zero falhas**. A execução
integral encontrou sete expectativas antigas de volume em test_audio_ui;
essas expectativas específicas da Mochila foram atualizadas para 0,65 e o
módulo foi reexecutado com sucesso, junto das dez regressões visuais novas.
Prévias adicionais: deck completo e filtro LV2.
