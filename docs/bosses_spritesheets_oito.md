# Octav, Jan-Pietro e Labrro — folhas nativas de oito quadros

> Referência vigente — auditoria de 23/11/2026. [Estado atual](estado_atual.md). Relatos de validações datadas abaixo representam somente aquela execução.

Integração retomada em 23/11/2026 após interrupção do computador. A inspeção
anterior e dois reparos ImageGen foram recuperados; o Git estava limpo antes
desta retomada. Nenhuma integração parcial precisou ser descartada.

## Origem e identidade

Pacote externo preservado: `BossesNovasSprites.zip`, 18 PNGs RGB de 1600×1194.
O xadrez estava pintado nas imagens, não era transparência real. A pasta Boss6
foi confirmada pelo usuário como **Labrro**, não Jozephino.

| Pasta | Nome visível | ID preservado | Sprite1 | Sprite2 | Sprite3 | Sprite4 | Sprite5 | Sprite6 |
|---|---|---|---|---|---|---|---|---|
| Boss1 | Octav, o lobisomem | guardiao_da_pedra / Guardião da Pedra | Garras | Defesa | Vigor | Ultimate / atk2 | Dano | Idle |
| Boss5 | Jan-Pietro, o Imortal | corpo_seco / Corpo Seco | Idle | Dano | Ultimate / atk4 | Corte rápido | Defesa/cura | Lâminas cruzadas |
| Boss6 | Labrro, o Carrasco | carrasco_da_vigilia / Carrasco da Vigília | Idle | Dano | Corte | Varredura | Vigor Escarlate | Ultimate / atk3 |

Os IDs de combate, saves, efeitos e áudio permanecem estáveis. Nenhum dano,
status, custo de ação, intervalo de especial ou regra de progressão foi alterado.
Jozephino e os outros chefes preservam suas animações anteriores.

## Auditoria e reparos

Inspeção visual das 18 folhas e seus **144 quadros**, complementada pelos atlas
depois do preparo e pela renderização nas arenas. Os números abaixo começam em
1 e seguem esquerda→direita, primeira linha e depois segunda linha.

| Pasta/folha | Quadros defeituosos | Tratamento |
|---|---|---|
| Boss1/Sprite4 | 4 e 6 | Corrigidos torso alongado, braço fundido ao urso e corpo translúcido/duplicado. A folha inteira foi recomposta com oito poses e separação entre células, mantendo a identidade das referências saudáveis. |
| Boss5/Sprite4 | 4 | A célula mostrava apenas projéteis. Personagem refeito entre as poses 3 e 5, com dois braços e duas adagas. Escala do reparo ajustada para os vizinhos. |
| Boss6/Sprite5 | 4 | Corrigida a continuidade do cabo do machado entre mãos e lâmina. Pose de canalização e aura vermelha preservadas. |
| Boss6/Sprite6 | 5, 6 e 7 | Corrigidos detritos compartilhados entre células, pés cortados em 6/7 e recuperação que erguia novamente o machado como outro golpe. Folha recomposta com um impacto e retorno à guarda. |

Nas outras poses não foram identificadas deformações anatômicas que exigissem
redesenho. Todas receberam remoção de matte, ajuste de margens reais, pivô,
escala e orientação. Saltos intencionais do Labrro são animados pelo deslocamento
da apresentação do especial, sem somar um salto acidental causado pelo recorte.

As correções raster foram feitas no ImageGen com as próprias folhas e poses
saudáveis como referências. Os originais gerados foram preservados fora dos
assets ativos. O manifesto registra SHA-256 do ZIP e de cada fonte de reparo,
motivo, ordem e caixas de extração dos quadros. O código não depende desses
arquivos externos para rodar o jogo.

## Contrato técnico

- Ativos canônicos: `assets/bosses/sheets_eight/<id>/<acao>.png`.
- São seis folhas por chefe, cada uma com grade 4×2, células RGBA de 448×320.
  A transparência é real; cores de pixels totalmente transparentes são zeradas.
- Ordem de carregamento: esquerda→direita, cima→baixo. Não misturar estas oito
  poses nativas com os intervalos artificiais das ações legadas de doze poses.
- Pés no pivô inferior preparado (linha 318), mesmo eixo; escala proporcional,
  sem deformação independente de largura/altura. Alturas de referência de corpo:
  Octav 156, Jan-Pietro 132 e Labrro 171 pixels antes da escala virtual da arena.
- O preparo respeita margens reais: as folhas originais têm poses/efeitos que
  atravessam as divisões ideais de 400×597; dividir o ZIP cegamente cortaria pés
  e armas. Os derivados finais já têm grade rigorosamente uniforme.
- A componente cinza do xadrez tingido por auras vira alfa real; não deixar
  quadrados opacos dentro de azul/verde. Reflexos internos da magia preservados.
- Paleta comum de 256 cores por chefe e remoção de fragmentos isolados castanhos.
- Idle: Octav/Labrro 225 ms; Jan-Pietro 160 ms com ciclo próprio. Dano: fontes de oito poses, com seleção segura nos 560 ms
  globais. Ataques e suporte usam o relógio existente, independente do FPS da
  janela; preparação/impacto/recuperação percorrem as oito poses uma vez.
- Os efeitos independentes de Ultimate continuam separados e conservados.
  O projétil `guardiao_da_pedra/urso_espiritual.png` continua ativo. A estrela
  vermelha de Vigor Escarlate continua no efeito de cast existente.

## Reprodução

Preparo canônico: `devtools/prepare_boss_sheet_update.py --zip <ZIP> --repairs <JSON> --preview <pasta>`.
O JSON de reparos associa `Boss1/Sprite4`, `Boss5/Sprite4`, `Boss6/Sprite5` e
`Boss6/Sprite6` a caminhos externos de `sheet` ou `frame`, quadro `index`, ajuste
proporcional opcional `multiplier`, lista `frames` e `reason`. Não regenerar esses
três chefes com os preparadores históricos de quatro/doze poses.

Piloto sem saves: `devtools/preview_boss_sheets.py --smoke --output <pasta>`.
Sem `--smoke`, `--boss 1`, `--boss 5` ou `--boss 6` mostra apenas o chefe escolhido.
O piloto exporta atlas das arenas e GIFs com repouso, ações, suporte, especial e
dano. A execução automática não comprova aprovação perceptual humana ou campanha
completa jogada.

## Limpeza e arquivos

**441 arquivos substituídos (36.309.211 bytes)** foram movidos para o arquivo
local ignorado `_arquivos_antigos_para_deletar/bosses_folhas_8_2026-11-23/`.
Inclui as pastas antigas destes três chefes em `bosses/eight_frames` e
`bosses/twelve_frames` e suas poses legadas de quatro quadros nas pastas raiz.
O urso independente não foi movido. Manifests antigos não anunciam os grupos
arquivados, e o carregador não mantém caminhos de poses substituídas.

Código criado/alterado:
- `src/systems/boss_sheet_kits.py` — mapeamento estável e amostragem de oito poses.
- `src/core/asset_manager.py` — fatiamento das folhas e retirada dos carregamentos antigos.
- `src/ui/entity_view.py` — cadência dos kits nativos, mantendo impacto e deslocamento melee.
- `src/systems/boss_animation_kits.py` — documentação dos kits mistos atuais.
- `devtools/prepare_boss_sheet_update.py` e `devtools/preview_boss_sheets.py`.

Ativos: 18 folhas, três paletas e um manifesto em `assets/bosses/sheets_eight/`;
manifests de oito/doze poses legadas atualizados.

Testes atualizados: `test_boss_twelve_frames`, `test_boss_ultimate_animations`,
`test_guardiao_da_pedra`, `test_carrasco_da_vigilia`, `test_corpo_seco_animation`,
`test_corpo_seco_visual_scale`; contrato novo em `test_boss_sheet_update`.
Relatório consolidado: `docs/validacao_bosses_folhas_oito.json`.

## Resultado da validação desta integração

- Suíte consolidada: **688 testes em 72 módulos, todos aprovados**. A primeira
  passagem apontou apenas a expectativa antiga de 12 poses no buff de Labrro;
  ela foi atualizada para 8 e o módulo reexecutado no relatório consolidado.
- Smoke do piloto aprovado para os três chefes: repouso, dano, ataques, suporte
  e Ultimate renderizados sem saves reais. Atlas de quadros e arenas inspecionados.
- Referências ativas às pastas de poses substituídas removidas; o arquivo local
  de versões antigas permanece ignorado pelo Git. Efeitos independentes e áudio
  mantiveram suas validações anteriores, inclusive os hashes das magias.

## Conferência isolada dos seis anexos de Jan-Pietro — 23/11/2026

Os seis anexos recebidos novamente foram comparados pixel a pixel com Boss5 no
ZIP: são as mesmas imagens. A integração de Jan-Pietro já estava presente na
pasta original do projeto; os ativos tratados foram preservados.

Mapeamento confirmado por conteúdo (a ordem dos anexos na conversa difere da
numeração das ações): Sprite1 → idle; Sprite2 → dano; Sprite3 → ultimate/atk4;
Sprite4 → atk1; Sprite5 → healer2/def; Sprite6 → atk3.

A conferência dos 48 quadros confirma RGBA, grade final 4×2, apoio, orientação
para a esquerda e corpo opaco em todas as poses, incluindo o quadro 4 refeito
da estocada. Regressões novas verificam o corpo e as cores de giro/regeneração/
cortes. Os 147 arquivos antigos deste chefe (11.536.018 bytes) continuam no
arquivo local ignorado da integração anterior, sem duplicar cópias.

Nesta conferência foram alterados devtools/preview_boss_sheets.py (seleção de
chefe também no smoke, repetição e pausa por clique no piloto interativo),
tests/test_corpo_seco_visual_scale.py (duas regressões), esta documentação e o
relatório consolidado. As seis folhas tratadas e o carregamento em combate já
estavam corretos; não foi necessário regenerá-los nem mudar regras.

Piloto focado: python -B devtools/preview_boss_sheets.py --boss 5 --output <pasta>.
Clique pausa/continua e ESC fecha. Para exportar sem janela, acrescente --smoke.

Conferência isolada concluída: 16 testes direcionados aprovados e exportação
somente de Jan-Pietro aprovada. Relatório consolidado incremental atualizado:
690 testes em 72 módulos, zero falhas (duas regressões novas nesta conferência).


## Correção de tremida de Jan-Pietro

A reprodução anterior descrita acima foi revista após o vídeo de combate.
Jan-Pietro usa agora apoio fixo (224,318), botas idênticas no idle, cadência
própria de 160 ms e transições de guarda comuns. Os outros chefes mantêm sua
cadência. Detalhes e validação em [jan_pietro_alinhamento.md](jan_pietro_alinhamento.md).
