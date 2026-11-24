# Reações de dano e idle de Jozephino — 23/11/2026

> Referência vigente — auditoria de 23/11/2026. [Estado atual](estado_atual.md). Relatos de validações datadas abaixo representam somente aquela execução.

## Diagnóstico

Vídeo de 6,6 segundos analisado junto dos sprites efetivamente carregados.
A alternância rígida das poses, o uso de armas/partículas na referência do apoio,
o retorno forçado ao primeiro idle e o fallback que rotacionava/achatava a
silhueta produziam mudanças bruscas. Também havia oito poses de idle de Jozephino
com altura opaca variando de 125 a 102 pixels (aproximadamente 18% de redução).

O pedido foi aplicado a **Jozephino, o Inventor**, ID interno goblin nerd.
O Boss6 do pacote externo continua sendo Labrro, conforme o mapeamento aprovado;
nenhum ID foi trocado. No checkout atual, Jozephino usa oito PNGs individuais,
não a folha Boss6. O carregamento e a ordem das folhas 4×2 dos outros três chefes
continuam intactos.

## Reprodução corrigida

- Reações com duração global de 560 ms, incluindo contato sustentado de
  aproximadamente 90 ms e recuperação mais longa.
- Apoio medido no corpo opaco e na faixa dos pés, descartando detritos isolados.
  Cada pose aceita é transladada para a âncora da guarda atual. Não há zoom,
  achatamento, rotação ou flip durante a reação.
- Validação de escala/silhueta: altura entre 90% e 110% da guarda, largura entre
  72% e 132%, coincidência de máscaras mínima de 0,82, sem recorte do corpo e
  com apoio exato após o deslocamento.
- Poses incompatíveis são omitidas da sequência. Não se insere um retorno à
  guarda entre poses sobreviventes. Sem poses compatíveis, usa-se a guarda
  íntegra com o mesmo recuo/flash; isso também atende os cinco modelos procedurais.
- Mistura limitada à área comum da silhueta dominante. O alfa original é
  restaurado para não engrossar bordas/pés, criar halos ou uma segunda silhueta.
- Recuo horizontal máximo de 12 pixels no canvas virtual (cerca de 8 px em
  janela 1280×720), com entrada e saída suaves; nenhum deslocamento vertical.
  Pulso âmbar curto, multiplicativo, preserva a transparência e a paleta.
- O relógio do idle fica congelado durante o dano e continua da mesma fase ao
  terminar. O voo do morcego usa esse relógio, evitando salto ao reagir.
- A próxima ação inimiga aguarda a reação terminar, inclusive em velocidade
  rápida. O hold é visual; não muda dano, energia, debuffs, drops ou saves.
- Zanzara usa a arte necromante aprovada, convertida para um canvas comum sem
  alterar sua escala no mundo. Poses que fazem a foice desaparecer são evitadas.

## Idle de Jozephino

A postura íntegra original é preservada como base. Oito variantes de respiração
em cache deslocam apenas cabeça/tronco em até dois pixels, sem escala, mantendo
os mesmos pixels nas botas. Reprodução de 160 ms por pose (6,25 FPS), em ida e
volta: 0,1,2,3,4,5,6,7,6,5,4,3,2,1. O ciclo dura 2,24 segundos. As antigas poses
com encolhimento não são alternadas no idle de combate.

## Auditoria por personagem

Todos os nomes abaixo recebem a duração, recuo, flash e recuperação corrigidos.
A seleção é adaptativa à guarda/fase de idle que estava visível no impacto;
a tabela registra a conferência na fase 725 ms. Índices são 1-based.

| Personagem | Quadros de dano reutilizados | Tratamento |
|---|---|---|
| Octav, o lobisomem | 5, 6, 8 | Apoio registrado + mistura |
| Alvar & Tekks, Rastreadores | 1, 2, 7, 8 | Apoio registrado + mistura |
| Jozephino, o Inventor | 1, 7, 8 | Apoio registrado + mistura |
| Sir Thomas, a Besta Fera | Nenhum | Guarda estável + recuo/flash |
| Jan-Pietro, o Imortal | Nenhum | Guarda estável + recuo/flash |
| Labrro, o Carrasco | 1, 2, 3, 5, 8 | Apoio registrado + mistura |
| Zanzara, Líder do Clã Moskar | 1, 8 | Apoio registrado + mistura |
| Tekks | 1, 8 | Apoio registrado + mistura |
| Slime | Nenhum | Guarda estável + recuo/flash |
| Viniurgo | Nenhum | Guarda estável + recuo/flash |
| Macaco Selvagem | Nenhum | Guarda estável + recuo/flash |
| Guerreiro da Mata | 1, 8 | Apoio registrado + mistura |
| Golem das Ruínas | 8 | Apoio registrado + mistura |
| Lagarto Couraçado | Nenhum | Guarda estável + recuo/flash |
| Putrefato do Pântano | Nenhum | Guarda estável + recuo/flash |
| Crocodilo Abissal | 1, 7, 8 | Apoio registrado + mistura |
| Esqueleto Saqueador | Nenhum | Guarda estável + recuo/flash |
| Morcego Sombrio | Nenhum | Guarda estável + recuo/flash |
| Centauro Vigia | Nenhum | Guarda estável + recuo/flash |
| Lutador Mascarado | 1, 8 | Apoio registrado + mistura |
| Vinimuth | 1, 8 | Apoio registrado + mistura |
| Mago do Santuário | Nenhum | Guarda estável + recuo/flash |
| Goblin | Nenhum | Modelo procedural sem deformação |
| Guarda Sombrio | Nenhum | Modelo procedural sem deformação |
| Ogro Ancestral | Nenhum | Modelo procedural sem deformação |
| Cavaleiro Caído | Nenhum | Modelo procedural sem deformação |
| Behemoth de Pedra | Nenhum | Modelo procedural sem deformação |

## Arquivos e validação

- src/ui/enemy_reactions.py: registro de apoio, seleção/mistura, curva, recuo,
  pulso e respiração estável de Jozephino; caches limitados.
- src/ui/entity_view.py: reação compartilhada, fase de idle preservada e
  remoção do fallback de rotação/achatamento somente dos inimigos.
- src/ui/zanzara_necromancer.py: canvas de reação alinhado à guarda aprovada.
- src/scenes/battle_scene.py: espera visual antes da ação seguinte.
- devtools/preview_enemy_reactions.py: piloto sem saves que usa BattleScene;
  --smoke exporta atlas, GIFs individuais, idle de Jozephino e coordenadas.
- tests/test_enemy_reactions.py: apoio nativo e no desenho da arena, endpoints,
  relógio, hold, fallback inválido, botas do idle e espera de ações.
- Regressões atualizadas em test_boss_twelve_frames e test_zanzara_necromancer:
  o contrato é uma reação íntegra, não a reprodução obrigatória de poses inválidas.

As 27 formas foram renderizadas em BattleScene e os atlas inspecionados.
A conferência cobre 22 conjuntos com sprites (incluindo duas fases da dupla)
e cinco modelos procedurais, sem ler/gravar saves reais. Os testes verificam
apoio nativo exato e baseline do desenho dentro de um pixel de reamostragem.
Isso não equivale a uma campanha completa jogada manualmente.

Os PNGs, spritesheets, arquivos originais, efeitos independentes e áudio não
foram alterados; não há arquivos de arte substituídos para arquivar.
Relatórios: docs/reacoes_dano_auditoria.json (176 poses fonte e amostras de arena)
e docs/validacao_reacoes_dano.json (suíte de testes).

Resultado consolidado: **721 testes em 76 módulos, zero falhas**. A suíte
integral foi executada por módulos isolados; após o ajuste da espera visual,
os módulos afetados de combate, áudio, saves, tutorial, cutscene e reações
foram reexecutados. As nove regressões novas cobrem o caminho real da arena.
