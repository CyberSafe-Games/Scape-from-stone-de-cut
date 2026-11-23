# AGENTS.md — Scape From Stone de Cut

> Referência vigente — auditoria de 23/11/2026. [Estado atual](docs/estado_atual.md). Relatos de validações datadas abaixo representam somente aquela execução.

Referência vigente, auditada em 23/11/2026 contra o código. Regras completas:
[estado atual](docs/estado_atual.md), [catálogo LV1/LV2](docs/cartas_e_estados.md)
e [auditoria de documentação/testes](docs/auditoria_documentacao_testes.md).
Relatórios marcados como históricos registram etapas anteriores; não definem
custos, caminhos ou comportamento atual.

## 1. Projeto e ambiente

Roguelite/deckbuilder por turnos em Python 3.12+ e Pygame. Textos, comentários e
documentação em pt-BR; código em inglês e indentação de quatro espaços.
Jaum Manel defende a tribo Stone The Cut do Clã Moskar. Interface dark fantasy
rústica, pixel art, verde-musgo, couro/madeira/pedra e ouro envelhecido.

- Trabalhe no checkout ativo confirmado pelo usuário. Não imponha caminhos
  absolutos de computadores de outros integrantes nem versões locais de Python.
- Dependências de execução: requirements.txt (pygame>=2.6.0). Pillow e NumPy
  são dependências de desenvolvimento em requirements-dev.txt.
- Canvas interno 1920×1080, janela inicial 1280×720, 60 FPS; F11/F10 alternam
  os modos. Converta mouse com map_to_virtual/get_virtual_mouse_pos.
- Mouse deve permitir toda a navegação. ESC e atalhos são complementares.

## 2. Arquitetura e persistência

- src/config: resolução, layout, tipografia, nomes de exibição, trilha e preços.
- src/systems: regras sem interface; não introduzir Pygame nas transações.
- src/models: entidades, cartas, ações e efeitos.
- src/scenes e src/ui: eventos, composição e animações. BaseScene/SceneManager
  administram cenas e modais. Áudio via scene_manager.audio_manager.
- src/settings.py e src/game.py são shims; não colocar regras novas neles.
- Saves v14: perfil permanente separado de run; progresso é o alias em memória.
  SaveManager valida/migra, usa revisão otimista e gravação atômica.
- Mudanças de schema exigem SAVE_VERSION e migração compatível. Não incrementar
  a versão por mudança visual/documental.
- Transações falhas restauram o documento completo. Preservar rascunho de deck,
  rollback, isolamento entre slots e semântica exclusiva de modo_teste.
- Derrota encerra a run, mantendo perfil/fragmentos; nova run refaz estado
  temporário. Há snapshot de combate para retomar uma luta viva; isso não
  equivale a recuperar uma run morta. Epílogo após Zanzara já está implementado.
- Preservar alterações preexistentes; não usar add global, stash, reset, restore
  ou descarte sem autorização. Commit, publicação e merge exigem autorização
  do usuário. Não publicar como parte de uma simples auditoria.

## 3. Campanha, nomes e IDs

Dois encontros comuns antes de cada chefe, sete territórios. IDs legados
permanecem estáveis em saves, áudio, sprites, retratos e regras.

| Nome interno | Nome exibido |
|---|---|
| Guardião da Pedra | Octav, o lobisomem |
| Álvaro e Tex | Alvar & Tekks, Rastreadores |
| Álvaro e Tex · Pequeno | Tekks |
| Goblin Nerd | Jozephino, o Inventor |
| Gordofera | Sir Thomas, a Besta Fera |
| Corpo Seco | Jan-Pietro, o Imortal |
| Carrasco da Vigília | Labrro, o Carrasco |
| Zanzara | Zanzara, Líder do Clã Moskar |

Use boss_display_name em src/config/boss_names.py; não renomeie Enemy.name,
boss_id, boss_key ou slugs para acompanhar mudanças narrativas.
O ZIP BossesNovasSprites usa Boss1=Octav, Boss5=Jan-Pietro e Boss6=Labrro.
Jozephino é goblin nerd, mesmo quando mensagens informais o chamarem Boss6.
Consulte o código/nome e esclareça divergências sem trocar personagens.

## 4. Combate e estados

- Energia inicial 2, teto 8 e crescimento por turno; melhorias permanentes podem
  alterar o início. Mão inicial 3, limite 5, cartas restantes ficam na mão.
- Deck: 6–18 cartas, três cópias por tipo. Pode haver rascunho vazio, mas só deck
  válido é promovido/salvo; não sobrescrever o último válido ao fechar.
- Cemitério: descarte por uma energia e uma troca grátis por turno.
- Intenções: uma ação comum, duas de chefe; executar o plano já anunciado.
- Revanche não gera ouro, cartas ou materiais; recompensas têm identificação
  idempotente por run/encontro. Não permitir farm por repetir etapa.
- Ultimate começa em ultimate_charge=0 em toda nova batalha, threshold=20.
  Não herdar carga de outra batalha nem do campo legado carga_ultimate.
  Retomar o snapshot da mesma luta viva restaura a carga daquela luta; a
  segunda fase da dupla também conserva o estado por ser a mesma batalha.
- Limpar debuffs, durações, contadores, Força e bônus temporários ao iniciar/
  encerrar combate; preservar somente os campos de progressão previstos.
- Veneno: 1–2 stacks por aplicação, máximo 5, poison_turns=2 renovado inclusive
  no teto. Fim do turno: 5*poison_stacks direto, sem Escudo; decrementar duração,
  zerar stacks ao expirar.
- Sangramento: 1–2 stacks, máximo 5, bleed_turns=2 renovado. Após ação ofensiva
  que tire vida do alvo: 3*bleed_stacks direto, se bleed_triggers_this_turn<2.
  Multigolpe conta uma ação. Resetar contador no início; reduzir duração no fim
  sem dano extra. Zerar stacks quando expirar.
- Choque: somente inimigos aplicam ao jogador. Cada stack tira uma energia no
  próximo início de turno, mínimo zero; consumir/remover todos imediatamente.
  Jozephino aplica um na descarga comum e dois no especial.
- HUD/tooltips mostram stacks, dano por gatilho e duração. Não tratar números
  antigos de Veneno/Sangramento como dano fixo.

## 5. Cartas, ultimates e evolução

Catálogo com 20 cartas disponíveis e 75 bloqueadas. CARD_SPECS/CARD_POOL são a
fonte; unavailable não entra em compra, recompensa nem equipamento.

- Arte LV1: assets/cards/<id>.png; LV2 prateada: assets/cards/lv2/<id>.png.
  assets/cards/art_manifest.json registra recortes, dimensões, contorno e
  centroide do losango de cada uma das 40 artes.
- Propagar level, cost e description da cópia real via instance_card para
  get_card_image. Cache por nível/custo/descrição. Não presumir redução de custo
  no LV2: usar as regras reais de roguelite.py.
- with_player_rules recompõe somente o interior do losango da arte: um custo
  dinâmico, sem badge duplicado. Não deslocar o contorno por coordenada global
  fixa. with_rules permanece para intenções/consumidores legados.
- Recortes regulares têm dimensões individuais registradas no manifesto;
  não presumir que as 40 imagens tenham a dimensão da Ultimate.
- Desenhar a carta inteira proporcionalmente; preservar transparência e padding
  entre carta e moldura externa, desenhando o ornamento por último.
- Ultimates: PNGs individuais completos 316×489, moldura dourada, exterior
  transparente, geometria da Esfera Protetora LV2. Manifesto assets/ultimates/art_manifest.json.
  Custo e rodapé são dinâmicos. Carga 20 e custo 2 para as três:
  Mana restaura energia para 8 e limpa negativos, sem comprar cartas;
  Forças concede +12 Força até o fim da luta e 40 Escudo/2 turnos;
  Rugido destrói Escudo antes de 60 de dano base e aplica Fraqueza/3 turnos,
  respeitando modificadores e proteções existentes.
- Evolução individual LV1→LV2: três materiais do tipo e preço UPGRADE_PRICES,
  limite de três upgrades por run. Material custa 15, reserva máxima 9.
  Não evoluir automaticamente todas as cópias.
- Preços das cartas em CARD_PRICES. Loja cura até 20 HP atual por 30/45/60 ouro,
  até três compras/run; não aumenta vida máxima. Vida cheia não cobra nem conta.
  Melhorias permanentes de vida/energia/preparação usam fragmentos entre runs.

## 6. Telas e interação

- Mercado Silencioso: cenário/mercador ilustrados, quatro cartas por página,
  preços, compra, cura e feedback. Altar: seleção da cópia, Antes LV1/Depois LV2,
  comparação calculada, materiais/preço e confirmação com efeitos.
- Mochila Ancestral: cenário de expedição, 18 compartimentos de couro, reserva
  em páginas de seis tipos, filtros e aba de ultimates. Preview fixo à direita,
  fora dos botões; hover nunca equipa/consome recursos.
- Filtros de custo/nível da Mochila acompanham a próxima cópia livre, priorizando
  LV2 como a regra existente. Recalcular após mutações do deck.
- Compartilhar composição MerchantWorkshopView/BackpackView; não duplicar
  transações de shop_system/roguelite/deck_loadout na UI.
- Intenção com arte: somente carta ampliada, sem painel lateral redundante,
  centralizada horizontalmente em y≈43% e limitada às bordas da tela.
  Ícones ficam no canto superior direito. Sem arte, usar ficha textual única.
  Preview é visual, desenhado acima da arena, sem capturar cliques.

## 7. Famílias de animação e personagens

O jogo tem kits mistos; não padronizar tudo em 4×2 ou doze quadros por engano.

- Octav/Jan-Pietro/Labrro: seis folhas RGBA nativas 4×2, oito frames row-major,
  células 448×320, em assets/bosses/sheets_eight/<slug>/, com paleta/manifesto.
  Carregamento AssetManager._load_boss_sheet_kit; aliases em boss_sheet_kits.py.
  Preparo canônico prepare_boss_sheet_update.py; não executar preparadores
  históricos de oito/doze poses para sobrescrever estes kits.
- Outros chefes legados: ações de doze poses; idle/fontes de dano de oito.
  Efeitos independentes de Ultimate podem ter doze frames; não confundir corpo,
  carta e camada de magia. A dupla mantém suas duas fases.
- Inimigos comuns: 14 tipos, oito frames, canvas 448×260. Não confundir o
  Golem das Ruínas com Octav.
- Protagonista esguio: ações/cartas/ultimates com doze poses, idle/dano com oito;
  preservar desenho, equipamentos, paleta e pivô.
- Jan-Pietro: apoio (224,318), botas pixel-idênticas no idle, 160 ms/pose, ciclo
  de respiração em jan_pietro_animation.py; não aplicar outro align_stance.
- Jozephino: oito respirações derivadas da guarda íntegra, botas fixas,
  160 ms/pose (6,25 FPS), ping-pong; não restaurar poses que encolhem 18%.
- Dano inimigo: enemy_reactions.py registra apoio e filtra poses incompatíveis,
  560 ms totais, hold visual ≈90 ms, recuo só horizontal até 12 px internos e
  pulso curto. Preservar fase de idle e esperar reação antes da ação seguinte.
  Não girar/achatar/redimensionar nem forçar poses inválidas por contagem.
- Zanzara: necromante de foice, kimono preto, efeitos verdes, habilidades Foice,
  Passo, Grilhões e Travessia/Caronte. Não restaurar moedas, amuleto ou palma.
  Renderizador e estados próprios; preservar escala, rosto aprovado em
  bosses/zanzara-necromante-v8.png e moldura do protagonista (framed-content).

## 8. Assets, áudio e limpeza

- Reutilizar material aprovado; não sobrescrever originais externos.
  Preparo reproduzível e fontes/prompts em docs/manifestos.
- Ao substituir recurso, verificar referências e mover para
  _arquivos_antigos_para_deletar/ (ignorado) ou remover o ativo obsoleto.
  Não comitar essa pasta, fontes temporárias, saves ou capturas de QA enormes.
- Não remover fundos/ornamentos compartilhados ainda referenciados.
- Caminhos relativos ao projeto, slugs estáveis, transparência real. Ausência
  de arquivo não deve ficar oculta por fallback em testes de integração.
- Arte intencionalmente alterada exige atualizar fixtures de hashes/pixels
  pertinentes; não alterar fixture só para silenciar falha.
- IDs de áudio estáveis via AudioManager; derivados novos em OGG com origem e
  composição registradas, preservando versões aprovadas.
- Trilha canônica em src/config/music.py: Deep forest menu/mapa/serviços,
  The Last Stand combates, Jungle Chase chefes, Jungle Tribe Zanzara.
  Volume inicial 45%, saída 350 ms e entrada 600 ms; canal musical separado.
  Não reiniciar música na mesma região/contexto nem na segunda fase da dupla.
- Não afirmar escuta crítica ou campanha completa jogada com base só em smoke.

## 9. Testes e conferência

Usar unittest, não pytest. Instalar requirements-dev.txt para testes de assets.
O executor por módulos evita acumular caches até faltar memória:

~~~powershell
python -m pip install -r requirements-dev.txt
python -B devtools/validate_isolated_tests.py --report docs/validacao_auditoria_documentacao.json
python -B devtools/audit_project_docs.py --output docs/auditoria_documentacao.json
~~~

Em Unix, usar python3 se necessário. SDL dummy é configurado pelo executor.
Um módulo isolado: configurar SDL_VIDEODRIVER/SDL_AUDIODRIVER=dummy e executar
python -m unittest tests.test_ultimate_cards_lv2 -v.
Resume/recheck são incrementais; não chamá-los de nova suíte integral.

- Rodar testes pertinentes e a suíte solicitada; não reduzir asserts para
  aceitar regressões. Expectativas antigas mudam somente com contrato aprovado.
- Durante ajuste de personagem, usar somente o piloto pertinente; no fechamento
  geral, testes sem janelas e no máximo uma instância do jogo para conferência.
- Pilotos usam --smoke com drivers definidos antes de importar Pygame e saves
  temporários. Não tocar nos três slots reais para QA.
- Atualizar documentação, inventário/contrato e relatório quando o código mudar.
  Ao concluir, informar arquivos, validação e limitações materiais.
