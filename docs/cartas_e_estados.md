# Cartas disponíveis, evolução e estados

> Referência vigente — auditoria de 23/11/2026. [Estado atual](estado_atual.md). Relatos de validações datadas abaixo representam somente aquela execução.

20 tipos disponíveis, 75 definições bloqueadas para compra, drops e deck.
Tabela extraída de CARD_SPECS e instance_card, sem inventar redução de custo LV2.
Artes completas LV1 padrão em assets/cards/ e LV2 prateadas em assets/cards/lv2/.
O manifesto geométrico registra contorno/centro do losango por arte; custo,
nível e descrição vêm da cópia real, com um único indicador dinâmico.

## Catálogo LV1 → LV2

| ID | Nome | Energia LV1 | Descrição LV1 | Energia LV2 | Descrição LV2 |
|---|---|---:|---|---:|---|
| esfera_protetora | Esfera Protetora | 1 | Receba 10 de Escudo por 2 turnos. | 1 | Receba 14 de Escudo por 2 turnos. |
| soco_simples | Soco Simples | 1 | Cause 6 de dano. | 1 | Cause 9 de dano. |
| investida | Investida | 2 | Cause 18 de dano. Depois, remova 25% do Escudo restante do inimigo, arredondando para baixo. | 2 | Cause 24 de dano. Depois, remova 25% do Escudo restante do inimigo, arredondando para baixo. |
| aura_rubra | Aura Rubra | 2 | Seus ataques causam +6 de dano por 3 turnos. Reaplicar renova a duração. | 2 | Seus ataques causam +8 de dano por 3 turnos. Reaplicar renova a duração. |
| pocao_fragilizante | Poção Fragilizante | 1 | Por 3 turnos, o inimigo recebe 25% a mais de dano de ataques. | 1 | Por 3 turnos, o inimigo recebe 25% a mais de dano de ataques. Receba também 5 de Escudo. |
| pocao_purificadora | Poção Purificadora | 1 | Remova todos os seus efeitos negativos. | 1 | Remova todos os seus efeitos negativos. Recupere 6 de vida. |
| totem_protetor | Totem Protetor | 3 | Ignore o próximo ataque inimigo inteiro. Não bloqueia dano de efeitos. | 3 | Ignore o próximo ataque inimigo inteiro. Não bloqueia dano de efeitos. Receba também 8 de Escudo. |
| zarabatana_venenosa | Zarabatana Venenosa | 3 | Dispare 3 dardos. Cause 10 de dano total e aplique 2 stacks de Veneno por 2 turnos. | 3 | Dispare 3 dardos. Cause 16 de dano total e aplique 2 stacks de Veneno por 2 turnos. |
| disparo_de_arco | Disparo de Arco | 2 | Cause 20 de dano à distância. | 2 | Cause 26 de dano à distância. |
| esfera_escudo | Esfera Escudo | 3 | Receba 32 de Escudo por 2 turnos. | 3 | Receba 42 de Escudo por 2 turnos. |
| machado_quebra_escudo | Machado Quebra-Escudo | 1 | Destrua todo o Escudo do inimigo. | 1 | Destrua todo o Escudo do inimigo. Receba também 8 de Escudo. |
| amuleto_dissipador | Amuleto Dissipador | 2 | Remova os efeitos positivos do inimigo, incluindo Escudo e Força. Preserve os efeitos negativos. | 2 | Remova os efeitos positivos do inimigo, incluindo Escudo e Força. Preserve os efeitos negativos. Receba também 8 de Escudo. |
| adaga_sangrenta | Adaga Sangrenta | 2 | Cause 8 de dano e aplique 2 stacks de Sangramento por 2 turnos. | 2 | Cause 14 de dano e aplique 2 stacks de Sangramento por 2 turnos. |
| mascara_ancestral | Máscara Ancestral | 4 | Recupere 14 de vida e receba 22 de Escudo por 2 turnos. | 4 | Recupere 18 de vida e receba 28 de Escudo por 2 turnos. |
| machados_gemeos | Machados Gêmeos | 5 | Cause 40 de dano. | 5 | Cause 50 de dano. |
| lanca_perfurante | Lança Perfurante | 3 | Cause 30 de dano. | 3 | Cause 38 de dano. |
| bola_de_fogo | Bola de Fogo | 2 | Cause 12 de dano e Fogo por 3 turnos: 3 de dano por intensidade ao fim do turno. Acumula até 3 intensidades e atinge Escudo primeiro. | 2 | Cause 18 de dano e Fogo por 3 turnos: 3 de dano por intensidade ao fim do turno. Acumula até 3 intensidades e atinge Escudo primeiro. |
| pocao_de_cura | Poção de Cura | 3 | Recupere 20 de vida, sem ultrapassar a vida máxima. | 3 | Recupere 26 de vida, sem ultrapassar a vida máxima. |
| surto_de_energia | Surto de Energia | 1 | Ganhe 2 de energia extra no próximo turno, até o limite de 8. Não aumenta sua energia máxima. | 1 | Ganhe 3 de energia extra no próximo turno, até o limite de 8. Não aumenta sua energia máxima. |
| pocao_venenosa | Poção Venenosa | 2 | Aplique 2 stacks de Veneno por 2 turnos. | 2 | Aplique 2 stacks de Veneno por 2 turnos. Receba também 6 de Escudo. |

## Evolução e disponibilidade

Três materiais do tipo + ouro de UPGRADE_PRICES evoluem somente a cópia escolhida.
Limite de três upgrades/run; material custa 15 ouro, reserva até nove por tipo.
O Altar compara Antes/Depois reais; Mochila/combate preservam o ID e nível.
As 75 definições adicionais não ficam disponíveis por existir fallback de arte;
seus textos experimentais não são regras de cartas jogáveis.

## Estados

- Veneno: 1–2 stacks/aplicação, máximo 5, duração renovada para 2 turnos.
  Fim do turno: 5×stacks direto, ignora Escudo, decrementa duração e zera ao expirar.
- Sangramento: 1–2 stacks, máximo 5, duração 2 renovável. Após ação ofensiva que
  tire vida do alvo: 3×stacks direto, no máximo duas ativações/turno. Multigolpe
  conta uma ação; reset do contador no início; duração decresce no fim sem tick.
- Choque: somente inimigo contra jogador; perde uma energia por stack no próximo
  início, mínimo zero; todos os stacks removidos após aplicar.
- Fogo segue intensidades/duração em entity.py e consome Escudo antes da vida.
  Vulnerável aumenta ataques em 25%; Fraqueza reduz dano base em 25%.
- Escudo usa camadas com duração própria. Totem bloqueia o próximo ataque inteiro,
  não dano contínuo. Purificação limpa negativos e preserva benefícios.
- Amuleto Dissipador remove positivos do inimigo, preservando negativos.

Resetar estados temporários ao iniciar/encerrar combate. Artes substituídas
ficam no arquivo local ignorado, fora das pastas ativas.
[Regras e ultimates vigentes](estado_atual.md).
Fontes: card_definitions.py, card_catalog.py, roguelite.py, tactical_card_effect.py
e entity.py. Testes: test_tactical_cards, test_roguelite, test_player_card_art,
test_merchant_workshop, test_backpack_visual e test_documentation_contract.
