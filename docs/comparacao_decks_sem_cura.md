# Comparação de decks sem cartas de cura

> **Registro histórico — não é especificação vigente.** Valores, caminhos, comandos e resultados abaixo pertencem à etapa original. Não restaurar regras/arte antigas nem executar preparadores sobre kits atuais. Consulte o [estado atual](estado_atual.md).

Teste automatizado, sem alterar regras do jogo ou saves reais. Referência LV1 e controle com até três LV2; 60 HP, energia inicial 2 e zero melhorias permanentes. A cura normal de 30% após chefes é preservada.

**LV1 usa dez sementes por política; o controle LV2 usa cinco. Cada célula agrupa duas políticas do bot (conservadora/agressiva): 20 ou 10 casos, não sementes independentes adicionais.** Limite de 40 turnos por confronto; limite não é contado como morte.

Na campanha controlada o deck completo está pronto desde o começo; na aquisição real, o jogo começa obrigatoriamente com Socos e Protetoras. O JSON marca `restricao_atendida` em cada encontro para não apresentar o deck inicial híbrido como dano ou defesa puros. Com LV2 habilitado, o controle recebe o deck final pronto; a aquisição real precisa pagar os materiais/evoluções.

## Composições

- **somente_dano**: 3× Soco Simples, 3× Disparo de Arco, 3× Lança Perfurante.
- **hibrido**: 2× Soco Simples, 2× Disparo de Arco, 3× Esfera Protetora, 2× Esfera Escudo.
- **somente_defesa**: 3× Esfera Protetora, 3× Esfera Escudo, 3× Totem Protetor.
- **dano_efeitos**: 3× Soco Simples, 3× Adaga Sangrenta, 3× Zarabatana Venenosa.
- **hibrido_efeitos**: 2× Adaga Sangrenta, 2× Zarabatana Venenosa, 3× Esfera Protetora, 2× Totem Protetor.
- **hibrido_controle**: 3× Disparo de Arco, 3× Esfera Protetora, 2× Esfera Escudo, 1× Poção Purificadora.
- **defesa_controle**: 3× Esfera Protetora, 3× Esfera Escudo, 2× Totem Protetor, 1× Poção Purificadora.

Todas as composições têm nove cópias e máximo de três por tipo. Defesa pura usa Escudo/Totem; defesa_controle acrescenta limpeza LV1. Nenhuma possui cura, reflexo ou efeito ofensivo.

## Campanhas completas

| Relatório | Ultimate | Cura na loja | LV2 | Deck | Modo | Vitórias/casos |
|---|---|---|---|---|---|---:|
| [comparacao_decks_cura_limitada_mana](comparacao_decks_cura_limitada_mana.json) | mana_ancestral | 3 curas: 30/45/60 ouro | Até 3 | somente_dano | controlada | 0/10 |
| [comparacao_decks_cura_limitada_mana](comparacao_decks_cura_limitada_mana.json) | mana_ancestral | 3 curas: 30/45/60 ouro | Até 3 | somente_dano | aquisicao_real | 0/10 |
| [comparacao_decks_cura_limitada_mana](comparacao_decks_cura_limitada_mana.json) | mana_ancestral | 3 curas: 30/45/60 ouro | Até 3 | hibrido | controlada | 0/10 |
| [comparacao_decks_cura_limitada_mana](comparacao_decks_cura_limitada_mana.json) | mana_ancestral | 3 curas: 30/45/60 ouro | Até 3 | hibrido | aquisicao_real | 0/10 |
| [comparacao_decks_cura_limitada_mana](comparacao_decks_cura_limitada_mana.json) | mana_ancestral | 3 curas: 30/45/60 ouro | Até 3 | somente_defesa | controlada | 0/10 |
| [comparacao_decks_cura_limitada_mana](comparacao_decks_cura_limitada_mana.json) | mana_ancestral | 3 curas: 30/45/60 ouro | Até 3 | somente_defesa | aquisicao_real | 0/10 |
| [comparacao_decks_cura_limitada_mana](comparacao_decks_cura_limitada_mana.json) | mana_ancestral | 3 curas: 30/45/60 ouro | Até 3 | dano_efeitos | controlada | 0/10 |
| [comparacao_decks_cura_limitada_mana](comparacao_decks_cura_limitada_mana.json) | mana_ancestral | 3 curas: 30/45/60 ouro | Até 3 | dano_efeitos | aquisicao_real | 0/10 |
| [comparacao_decks_cura_limitada_mana](comparacao_decks_cura_limitada_mana.json) | mana_ancestral | 3 curas: 30/45/60 ouro | Até 3 | hibrido_efeitos | controlada | 0/10 |
| [comparacao_decks_cura_limitada_mana](comparacao_decks_cura_limitada_mana.json) | mana_ancestral | 3 curas: 30/45/60 ouro | Até 3 | hibrido_efeitos | aquisicao_real | 0/10 |
| [comparacao_decks_cura_limitada_mana](comparacao_decks_cura_limitada_mana.json) | mana_ancestral | 3 curas: 30/45/60 ouro | Até 3 | hibrido_controle | controlada | 0/10 |
| [comparacao_decks_cura_limitada_mana](comparacao_decks_cura_limitada_mana.json) | mana_ancestral | 3 curas: 30/45/60 ouro | Até 3 | hibrido_controle | aquisicao_real | 0/10 |
| [comparacao_decks_cura_limitada_mana](comparacao_decks_cura_limitada_mana.json) | mana_ancestral | 3 curas: 30/45/60 ouro | Até 3 | defesa_controle | controlada | 0/10 |
| [comparacao_decks_cura_limitada_mana](comparacao_decks_cura_limitada_mana.json) | mana_ancestral | 3 curas: 30/45/60 ouro | Até 3 | defesa_controle | aquisicao_real | 0/10 |
| [comparacao_decks_cura_limitada_rugido](comparacao_decks_cura_limitada_rugido.json) | rugido_da_floresta | 3 curas: 30/45/60 ouro | Até 3 | somente_dano | controlada | 0/10 |
| [comparacao_decks_cura_limitada_rugido](comparacao_decks_cura_limitada_rugido.json) | rugido_da_floresta | 3 curas: 30/45/60 ouro | Até 3 | somente_dano | aquisicao_real | 0/10 |
| [comparacao_decks_cura_limitada_rugido](comparacao_decks_cura_limitada_rugido.json) | rugido_da_floresta | 3 curas: 30/45/60 ouro | Até 3 | hibrido | controlada | 0/10 |
| [comparacao_decks_cura_limitada_rugido](comparacao_decks_cura_limitada_rugido.json) | rugido_da_floresta | 3 curas: 30/45/60 ouro | Até 3 | hibrido | aquisicao_real | 0/10 |
| [comparacao_decks_cura_limitada_rugido](comparacao_decks_cura_limitada_rugido.json) | rugido_da_floresta | 3 curas: 30/45/60 ouro | Até 3 | somente_defesa | controlada | 0/10 |
| [comparacao_decks_cura_limitada_rugido](comparacao_decks_cura_limitada_rugido.json) | rugido_da_floresta | 3 curas: 30/45/60 ouro | Até 3 | somente_defesa | aquisicao_real | 0/10 |
| [comparacao_decks_cura_limitada_rugido](comparacao_decks_cura_limitada_rugido.json) | rugido_da_floresta | 3 curas: 30/45/60 ouro | Até 3 | dano_efeitos | controlada | 0/10 |
| [comparacao_decks_cura_limitada_rugido](comparacao_decks_cura_limitada_rugido.json) | rugido_da_floresta | 3 curas: 30/45/60 ouro | Até 3 | dano_efeitos | aquisicao_real | 0/10 |
| [comparacao_decks_cura_limitada_rugido](comparacao_decks_cura_limitada_rugido.json) | rugido_da_floresta | 3 curas: 30/45/60 ouro | Até 3 | hibrido_efeitos | controlada | 0/10 |
| [comparacao_decks_cura_limitada_rugido](comparacao_decks_cura_limitada_rugido.json) | rugido_da_floresta | 3 curas: 30/45/60 ouro | Até 3 | hibrido_efeitos | aquisicao_real | 0/10 |
| [comparacao_decks_cura_limitada_rugido](comparacao_decks_cura_limitada_rugido.json) | rugido_da_floresta | 3 curas: 30/45/60 ouro | Até 3 | hibrido_controle | controlada | 0/10 |
| [comparacao_decks_cura_limitada_rugido](comparacao_decks_cura_limitada_rugido.json) | rugido_da_floresta | 3 curas: 30/45/60 ouro | Até 3 | hibrido_controle | aquisicao_real | 0/10 |
| [comparacao_decks_cura_limitada_rugido](comparacao_decks_cura_limitada_rugido.json) | rugido_da_floresta | 3 curas: 30/45/60 ouro | Até 3 | defesa_controle | controlada | 2/10 |
| [comparacao_decks_cura_limitada_rugido](comparacao_decks_cura_limitada_rugido.json) | rugido_da_floresta | 3 curas: 30/45/60 ouro | Até 3 | defesa_controle | aquisicao_real | 4/10 |
| [comparacao_decks_cura_limitada_sem_ultimate](comparacao_decks_cura_limitada_sem_ultimate.json) | nenhuma | 3 curas: 30/45/60 ouro | Até 3 | somente_dano | controlada | 0/10 |
| [comparacao_decks_cura_limitada_sem_ultimate](comparacao_decks_cura_limitada_sem_ultimate.json) | nenhuma | 3 curas: 30/45/60 ouro | Até 3 | somente_dano | aquisicao_real | 0/10 |
| [comparacao_decks_cura_limitada_sem_ultimate](comparacao_decks_cura_limitada_sem_ultimate.json) | nenhuma | 3 curas: 30/45/60 ouro | Até 3 | hibrido | controlada | 0/10 |
| [comparacao_decks_cura_limitada_sem_ultimate](comparacao_decks_cura_limitada_sem_ultimate.json) | nenhuma | 3 curas: 30/45/60 ouro | Até 3 | hibrido | aquisicao_real | 0/10 |
| [comparacao_decks_cura_limitada_sem_ultimate](comparacao_decks_cura_limitada_sem_ultimate.json) | nenhuma | 3 curas: 30/45/60 ouro | Até 3 | somente_defesa | controlada | 0/10 |
| [comparacao_decks_cura_limitada_sem_ultimate](comparacao_decks_cura_limitada_sem_ultimate.json) | nenhuma | 3 curas: 30/45/60 ouro | Até 3 | somente_defesa | aquisicao_real | 0/10 |
| [comparacao_decks_cura_limitada_sem_ultimate](comparacao_decks_cura_limitada_sem_ultimate.json) | nenhuma | 3 curas: 30/45/60 ouro | Até 3 | dano_efeitos | controlada | 0/10 |
| [comparacao_decks_cura_limitada_sem_ultimate](comparacao_decks_cura_limitada_sem_ultimate.json) | nenhuma | 3 curas: 30/45/60 ouro | Até 3 | dano_efeitos | aquisicao_real | 0/10 |
| [comparacao_decks_cura_limitada_sem_ultimate](comparacao_decks_cura_limitada_sem_ultimate.json) | nenhuma | 3 curas: 30/45/60 ouro | Até 3 | hibrido_efeitos | controlada | 0/10 |
| [comparacao_decks_cura_limitada_sem_ultimate](comparacao_decks_cura_limitada_sem_ultimate.json) | nenhuma | 3 curas: 30/45/60 ouro | Até 3 | hibrido_efeitos | aquisicao_real | 0/10 |
| [comparacao_decks_cura_limitada_sem_ultimate](comparacao_decks_cura_limitada_sem_ultimate.json) | nenhuma | 3 curas: 30/45/60 ouro | Até 3 | hibrido_controle | controlada | 0/10 |
| [comparacao_decks_cura_limitada_sem_ultimate](comparacao_decks_cura_limitada_sem_ultimate.json) | nenhuma | 3 curas: 30/45/60 ouro | Até 3 | hibrido_controle | aquisicao_real | 0/10 |
| [comparacao_decks_cura_limitada_sem_ultimate](comparacao_decks_cura_limitada_sem_ultimate.json) | nenhuma | 3 curas: 30/45/60 ouro | Até 3 | defesa_controle | controlada | 0/10 |
| [comparacao_decks_cura_limitada_sem_ultimate](comparacao_decks_cura_limitada_sem_ultimate.json) | nenhuma | 3 curas: 30/45/60 ouro | Até 3 | defesa_controle | aquisicao_real | 0/10 |
| [comparacao_decks_efeitos_mana](comparacao_decks_efeitos_mana.json) | mana_ancestral | Não | Não | dano_efeitos | controlada | 0/20 |
| [comparacao_decks_efeitos_mana](comparacao_decks_efeitos_mana.json) | mana_ancestral | Não | Não | dano_efeitos | aquisicao_real | 0/20 |
| [comparacao_decks_efeitos_mana](comparacao_decks_efeitos_mana.json) | mana_ancestral | Não | Não | hibrido_efeitos | controlada | 0/20 |
| [comparacao_decks_efeitos_mana](comparacao_decks_efeitos_mana.json) | mana_ancestral | Não | Não | hibrido_efeitos | aquisicao_real | 0/20 |
| [comparacao_decks_efeitos_mana_loja](comparacao_decks_efeitos_mana_loja.json) | mana_ancestral | 30 ouro, ilimitada (histórico) | Não | dano_efeitos | controlada | 0/20 |
| [comparacao_decks_efeitos_mana_loja](comparacao_decks_efeitos_mana_loja.json) | mana_ancestral | 30 ouro, ilimitada (histórico) | Não | dano_efeitos | aquisicao_real | 0/20 |
| [comparacao_decks_efeitos_mana_loja](comparacao_decks_efeitos_mana_loja.json) | mana_ancestral | 30 ouro, ilimitada (histórico) | Não | hibrido_efeitos | controlada | 0/20 |
| [comparacao_decks_efeitos_mana_loja](comparacao_decks_efeitos_mana_loja.json) | mana_ancestral | 30 ouro, ilimitada (histórico) | Não | hibrido_efeitos | aquisicao_real | 0/20 |
| [comparacao_decks_efeitos_rugido](comparacao_decks_efeitos_rugido.json) | rugido_da_floresta | Não | Não | dano_efeitos | controlada | 0/20 |
| [comparacao_decks_efeitos_rugido](comparacao_decks_efeitos_rugido.json) | rugido_da_floresta | Não | Não | dano_efeitos | aquisicao_real | 0/20 |
| [comparacao_decks_efeitos_rugido](comparacao_decks_efeitos_rugido.json) | rugido_da_floresta | Não | Não | hibrido_efeitos | controlada | 0/20 |
| [comparacao_decks_efeitos_rugido](comparacao_decks_efeitos_rugido.json) | rugido_da_floresta | Não | Não | hibrido_efeitos | aquisicao_real | 0/20 |
| [comparacao_decks_efeitos_rugido_loja](comparacao_decks_efeitos_rugido_loja.json) | rugido_da_floresta | 30 ouro, ilimitada (histórico) | Não | dano_efeitos | controlada | 0/20 |
| [comparacao_decks_efeitos_rugido_loja](comparacao_decks_efeitos_rugido_loja.json) | rugido_da_floresta | 30 ouro, ilimitada (histórico) | Não | dano_efeitos | aquisicao_real | 0/20 |
| [comparacao_decks_efeitos_rugido_loja](comparacao_decks_efeitos_rugido_loja.json) | rugido_da_floresta | 30 ouro, ilimitada (histórico) | Não | hibrido_efeitos | controlada | 0/20 |
| [comparacao_decks_efeitos_rugido_loja](comparacao_decks_efeitos_rugido_loja.json) | rugido_da_floresta | 30 ouro, ilimitada (histórico) | Não | hibrido_efeitos | aquisicao_real | 0/20 |
| [comparacao_decks_efeitos_sem_ultimate](comparacao_decks_efeitos_sem_ultimate.json) | nenhuma | Não | Não | dano_efeitos | controlada | 0/20 |
| [comparacao_decks_efeitos_sem_ultimate](comparacao_decks_efeitos_sem_ultimate.json) | nenhuma | Não | Não | dano_efeitos | aquisicao_real | 0/20 |
| [comparacao_decks_efeitos_sem_ultimate](comparacao_decks_efeitos_sem_ultimate.json) | nenhuma | Não | Não | hibrido_efeitos | controlada | 0/20 |
| [comparacao_decks_efeitos_sem_ultimate](comparacao_decks_efeitos_sem_ultimate.json) | nenhuma | Não | Não | hibrido_efeitos | aquisicao_real | 0/20 |
| [comparacao_decks_efeitos_sem_ultimate_loja](comparacao_decks_efeitos_sem_ultimate_loja.json) | nenhuma | 30 ouro, ilimitada (histórico) | Não | dano_efeitos | controlada | 0/20 |
| [comparacao_decks_efeitos_sem_ultimate_loja](comparacao_decks_efeitos_sem_ultimate_loja.json) | nenhuma | 30 ouro, ilimitada (histórico) | Não | dano_efeitos | aquisicao_real | 0/20 |
| [comparacao_decks_efeitos_sem_ultimate_loja](comparacao_decks_efeitos_sem_ultimate_loja.json) | nenhuma | 30 ouro, ilimitada (histórico) | Não | hibrido_efeitos | controlada | 0/20 |
| [comparacao_decks_efeitos_sem_ultimate_loja](comparacao_decks_efeitos_sem_ultimate_loja.json) | nenhuma | 30 ouro, ilimitada (histórico) | Não | hibrido_efeitos | aquisicao_real | 0/20 |
| [comparacao_decks_lv2_mana_loja](comparacao_decks_lv2_mana_loja.json) | mana_ancestral | 30 ouro, ilimitada (histórico) | Até 3 | somente_dano | controlada | 0/10 |
| [comparacao_decks_lv2_mana_loja](comparacao_decks_lv2_mana_loja.json) | mana_ancestral | 30 ouro, ilimitada (histórico) | Até 3 | somente_dano | aquisicao_real | 0/10 |
| [comparacao_decks_lv2_mana_loja](comparacao_decks_lv2_mana_loja.json) | mana_ancestral | 30 ouro, ilimitada (histórico) | Até 3 | hibrido | controlada | 0/10 |
| [comparacao_decks_lv2_mana_loja](comparacao_decks_lv2_mana_loja.json) | mana_ancestral | 30 ouro, ilimitada (histórico) | Até 3 | hibrido | aquisicao_real | 1/10 |
| [comparacao_decks_lv2_mana_loja](comparacao_decks_lv2_mana_loja.json) | mana_ancestral | 30 ouro, ilimitada (histórico) | Até 3 | somente_defesa | controlada | 0/10 |
| [comparacao_decks_lv2_mana_loja](comparacao_decks_lv2_mana_loja.json) | mana_ancestral | 30 ouro, ilimitada (histórico) | Até 3 | somente_defesa | aquisicao_real | 0/10 |
| [comparacao_decks_lv2_mana_loja](comparacao_decks_lv2_mana_loja.json) | mana_ancestral | 30 ouro, ilimitada (histórico) | Até 3 | dano_efeitos | controlada | 0/10 |
| [comparacao_decks_lv2_mana_loja](comparacao_decks_lv2_mana_loja.json) | mana_ancestral | 30 ouro, ilimitada (histórico) | Até 3 | dano_efeitos | aquisicao_real | 0/10 |
| [comparacao_decks_lv2_mana_loja](comparacao_decks_lv2_mana_loja.json) | mana_ancestral | 30 ouro, ilimitada (histórico) | Até 3 | hibrido_efeitos | controlada | 0/10 |
| [comparacao_decks_lv2_mana_loja](comparacao_decks_lv2_mana_loja.json) | mana_ancestral | 30 ouro, ilimitada (histórico) | Até 3 | hibrido_efeitos | aquisicao_real | 0/10 |
| [comparacao_decks_lv2_mana_loja](comparacao_decks_lv2_mana_loja.json) | mana_ancestral | 30 ouro, ilimitada (histórico) | Até 3 | hibrido_controle | controlada | 6/10 |
| [comparacao_decks_lv2_mana_loja](comparacao_decks_lv2_mana_loja.json) | mana_ancestral | 30 ouro, ilimitada (histórico) | Até 3 | hibrido_controle | aquisicao_real | 5/10 |
| [comparacao_decks_lv2_mana_loja](comparacao_decks_lv2_mana_loja.json) | mana_ancestral | 30 ouro, ilimitada (histórico) | Até 3 | defesa_controle | controlada | 0/10 |
| [comparacao_decks_lv2_mana_loja](comparacao_decks_lv2_mana_loja.json) | mana_ancestral | 30 ouro, ilimitada (histórico) | Até 3 | defesa_controle | aquisicao_real | 0/10 |
| [comparacao_decks_lv2_rugido_loja](comparacao_decks_lv2_rugido_loja.json) | rugido_da_floresta | 30 ouro, ilimitada (histórico) | Até 3 | somente_dano | controlada | 0/10 |
| [comparacao_decks_lv2_rugido_loja](comparacao_decks_lv2_rugido_loja.json) | rugido_da_floresta | 30 ouro, ilimitada (histórico) | Até 3 | somente_dano | aquisicao_real | 0/10 |
| [comparacao_decks_lv2_rugido_loja](comparacao_decks_lv2_rugido_loja.json) | rugido_da_floresta | 30 ouro, ilimitada (histórico) | Até 3 | hibrido | controlada | 0/10 |
| [comparacao_decks_lv2_rugido_loja](comparacao_decks_lv2_rugido_loja.json) | rugido_da_floresta | 30 ouro, ilimitada (histórico) | Até 3 | hibrido | aquisicao_real | 0/10 |
| [comparacao_decks_lv2_rugido_loja](comparacao_decks_lv2_rugido_loja.json) | rugido_da_floresta | 30 ouro, ilimitada (histórico) | Até 3 | somente_defesa | controlada | 0/10 |
| [comparacao_decks_lv2_rugido_loja](comparacao_decks_lv2_rugido_loja.json) | rugido_da_floresta | 30 ouro, ilimitada (histórico) | Até 3 | somente_defesa | aquisicao_real | 0/10 |
| [comparacao_decks_lv2_rugido_loja](comparacao_decks_lv2_rugido_loja.json) | rugido_da_floresta | 30 ouro, ilimitada (histórico) | Até 3 | dano_efeitos | controlada | 0/10 |
| [comparacao_decks_lv2_rugido_loja](comparacao_decks_lv2_rugido_loja.json) | rugido_da_floresta | 30 ouro, ilimitada (histórico) | Até 3 | dano_efeitos | aquisicao_real | 0/10 |
| [comparacao_decks_lv2_rugido_loja](comparacao_decks_lv2_rugido_loja.json) | rugido_da_floresta | 30 ouro, ilimitada (histórico) | Até 3 | hibrido_efeitos | controlada | 0/10 |
| [comparacao_decks_lv2_rugido_loja](comparacao_decks_lv2_rugido_loja.json) | rugido_da_floresta | 30 ouro, ilimitada (histórico) | Até 3 | hibrido_efeitos | aquisicao_real | 0/10 |
| [comparacao_decks_lv2_rugido_loja](comparacao_decks_lv2_rugido_loja.json) | rugido_da_floresta | 30 ouro, ilimitada (histórico) | Até 3 | hibrido_controle | controlada | 6/10 |
| [comparacao_decks_lv2_rugido_loja](comparacao_decks_lv2_rugido_loja.json) | rugido_da_floresta | 30 ouro, ilimitada (histórico) | Até 3 | hibrido_controle | aquisicao_real | 2/10 |
| [comparacao_decks_lv2_rugido_loja](comparacao_decks_lv2_rugido_loja.json) | rugido_da_floresta | 30 ouro, ilimitada (histórico) | Até 3 | defesa_controle | controlada | 7/10 |
| [comparacao_decks_lv2_rugido_loja](comparacao_decks_lv2_rugido_loja.json) | rugido_da_floresta | 30 ouro, ilimitada (histórico) | Até 3 | defesa_controle | aquisicao_real | 8/10 |
| [comparacao_decks_lv2_sem_ultimate_loja](comparacao_decks_lv2_sem_ultimate_loja.json) | nenhuma | 30 ouro, ilimitada (histórico) | Até 3 | somente_dano | controlada | 0/10 |
| [comparacao_decks_lv2_sem_ultimate_loja](comparacao_decks_lv2_sem_ultimate_loja.json) | nenhuma | 30 ouro, ilimitada (histórico) | Até 3 | somente_dano | aquisicao_real | 0/10 |
| [comparacao_decks_lv2_sem_ultimate_loja](comparacao_decks_lv2_sem_ultimate_loja.json) | nenhuma | 30 ouro, ilimitada (histórico) | Até 3 | hibrido | controlada | 0/10 |
| [comparacao_decks_lv2_sem_ultimate_loja](comparacao_decks_lv2_sem_ultimate_loja.json) | nenhuma | 30 ouro, ilimitada (histórico) | Até 3 | hibrido | aquisicao_real | 0/10 |
| [comparacao_decks_lv2_sem_ultimate_loja](comparacao_decks_lv2_sem_ultimate_loja.json) | nenhuma | 30 ouro, ilimitada (histórico) | Até 3 | somente_defesa | controlada | 0/10 |
| [comparacao_decks_lv2_sem_ultimate_loja](comparacao_decks_lv2_sem_ultimate_loja.json) | nenhuma | 30 ouro, ilimitada (histórico) | Até 3 | somente_defesa | aquisicao_real | 0/10 |
| [comparacao_decks_lv2_sem_ultimate_loja](comparacao_decks_lv2_sem_ultimate_loja.json) | nenhuma | 30 ouro, ilimitada (histórico) | Até 3 | dano_efeitos | controlada | 0/10 |
| [comparacao_decks_lv2_sem_ultimate_loja](comparacao_decks_lv2_sem_ultimate_loja.json) | nenhuma | 30 ouro, ilimitada (histórico) | Até 3 | dano_efeitos | aquisicao_real | 0/10 |
| [comparacao_decks_lv2_sem_ultimate_loja](comparacao_decks_lv2_sem_ultimate_loja.json) | nenhuma | 30 ouro, ilimitada (histórico) | Até 3 | hibrido_efeitos | controlada | 0/10 |
| [comparacao_decks_lv2_sem_ultimate_loja](comparacao_decks_lv2_sem_ultimate_loja.json) | nenhuma | 30 ouro, ilimitada (histórico) | Até 3 | hibrido_efeitos | aquisicao_real | 0/10 |
| [comparacao_decks_lv2_sem_ultimate_loja](comparacao_decks_lv2_sem_ultimate_loja.json) | nenhuma | 30 ouro, ilimitada (histórico) | Até 3 | hibrido_controle | controlada | 4/10 |
| [comparacao_decks_lv2_sem_ultimate_loja](comparacao_decks_lv2_sem_ultimate_loja.json) | nenhuma | 30 ouro, ilimitada (histórico) | Até 3 | hibrido_controle | aquisicao_real | 0/10 |
| [comparacao_decks_lv2_sem_ultimate_loja](comparacao_decks_lv2_sem_ultimate_loja.json) | nenhuma | 30 ouro, ilimitada (histórico) | Até 3 | defesa_controle | controlada | 0/10 |
| [comparacao_decks_lv2_sem_ultimate_loja](comparacao_decks_lv2_sem_ultimate_loja.json) | nenhuma | 30 ouro, ilimitada (histórico) | Até 3 | defesa_controle | aquisicao_real | 0/10 |
| [comparacao_decks_mana](comparacao_decks_mana.json) | mana_ancestral | Não | Não | somente_dano | controlada | 0/20 |
| [comparacao_decks_mana](comparacao_decks_mana.json) | mana_ancestral | Não | Não | somente_dano | aquisicao_real | 0/20 |
| [comparacao_decks_mana](comparacao_decks_mana.json) | mana_ancestral | Não | Não | hibrido | controlada | 0/20 |
| [comparacao_decks_mana](comparacao_decks_mana.json) | mana_ancestral | Não | Não | hibrido | aquisicao_real | 0/20 |
| [comparacao_decks_mana](comparacao_decks_mana.json) | mana_ancestral | Não | Não | somente_defesa | controlada | 0/20 |
| [comparacao_decks_mana](comparacao_decks_mana.json) | mana_ancestral | Não | Não | somente_defesa | aquisicao_real | 0/20 |
| [comparacao_decks_mana_loja](comparacao_decks_mana_loja.json) | mana_ancestral | 30 ouro, ilimitada (histórico) | Não | somente_dano | controlada | 0/20 |
| [comparacao_decks_mana_loja](comparacao_decks_mana_loja.json) | mana_ancestral | 30 ouro, ilimitada (histórico) | Não | somente_dano | aquisicao_real | 0/20 |
| [comparacao_decks_mana_loja](comparacao_decks_mana_loja.json) | mana_ancestral | 30 ouro, ilimitada (histórico) | Não | hibrido | controlada | 1/20 |
| [comparacao_decks_mana_loja](comparacao_decks_mana_loja.json) | mana_ancestral | 30 ouro, ilimitada (histórico) | Não | hibrido | aquisicao_real | 0/20 |
| [comparacao_decks_mana_loja](comparacao_decks_mana_loja.json) | mana_ancestral | 30 ouro, ilimitada (histórico) | Não | somente_defesa | controlada | 0/20 |
| [comparacao_decks_mana_loja](comparacao_decks_mana_loja.json) | mana_ancestral | 30 ouro, ilimitada (histórico) | Não | somente_defesa | aquisicao_real | 0/20 |
| [comparacao_decks_rugido](comparacao_decks_rugido.json) | rugido_da_floresta | Não | Não | somente_dano | controlada | 0/20 |
| [comparacao_decks_rugido](comparacao_decks_rugido.json) | rugido_da_floresta | Não | Não | somente_dano | aquisicao_real | 0/20 |
| [comparacao_decks_rugido](comparacao_decks_rugido.json) | rugido_da_floresta | Não | Não | hibrido | controlada | 0/20 |
| [comparacao_decks_rugido](comparacao_decks_rugido.json) | rugido_da_floresta | Não | Não | hibrido | aquisicao_real | 0/20 |
| [comparacao_decks_rugido](comparacao_decks_rugido.json) | rugido_da_floresta | Não | Não | somente_defesa | controlada | 0/20 |
| [comparacao_decks_rugido](comparacao_decks_rugido.json) | rugido_da_floresta | Não | Não | somente_defesa | aquisicao_real | 0/20 |
| [comparacao_decks_rugido_loja](comparacao_decks_rugido_loja.json) | rugido_da_floresta | 30 ouro, ilimitada (histórico) | Não | somente_dano | controlada | 0/20 |
| [comparacao_decks_rugido_loja](comparacao_decks_rugido_loja.json) | rugido_da_floresta | 30 ouro, ilimitada (histórico) | Não | somente_dano | aquisicao_real | 0/20 |
| [comparacao_decks_rugido_loja](comparacao_decks_rugido_loja.json) | rugido_da_floresta | 30 ouro, ilimitada (histórico) | Não | hibrido | controlada | 0/20 |
| [comparacao_decks_rugido_loja](comparacao_decks_rugido_loja.json) | rugido_da_floresta | 30 ouro, ilimitada (histórico) | Não | hibrido | aquisicao_real | 0/20 |
| [comparacao_decks_rugido_loja](comparacao_decks_rugido_loja.json) | rugido_da_floresta | 30 ouro, ilimitada (histórico) | Não | somente_defesa | controlada | 1/20 |
| [comparacao_decks_rugido_loja](comparacao_decks_rugido_loja.json) | rugido_da_floresta | 30 ouro, ilimitada (histórico) | Não | somente_defesa | aquisicao_real | 0/20 |
| [comparacao_decks_sem_ultimate](comparacao_decks_sem_ultimate.json) | nenhuma | Não | Não | somente_dano | controlada | 0/20 |
| [comparacao_decks_sem_ultimate](comparacao_decks_sem_ultimate.json) | nenhuma | Não | Não | somente_dano | aquisicao_real | 0/20 |
| [comparacao_decks_sem_ultimate](comparacao_decks_sem_ultimate.json) | nenhuma | Não | Não | hibrido | controlada | 0/20 |
| [comparacao_decks_sem_ultimate](comparacao_decks_sem_ultimate.json) | nenhuma | Não | Não | hibrido | aquisicao_real | 0/20 |
| [comparacao_decks_sem_ultimate](comparacao_decks_sem_ultimate.json) | nenhuma | Não | Não | somente_defesa | controlada | 0/20 |
| [comparacao_decks_sem_ultimate](comparacao_decks_sem_ultimate.json) | nenhuma | Não | Não | somente_defesa | aquisicao_real | 0/20 |
| [comparacao_decks_sem_ultimate_loja](comparacao_decks_sem_ultimate_loja.json) | nenhuma | 30 ouro, ilimitada (histórico) | Não | somente_dano | controlada | 0/20 |
| [comparacao_decks_sem_ultimate_loja](comparacao_decks_sem_ultimate_loja.json) | nenhuma | 30 ouro, ilimitada (histórico) | Não | somente_dano | aquisicao_real | 0/20 |
| [comparacao_decks_sem_ultimate_loja](comparacao_decks_sem_ultimate_loja.json) | nenhuma | 30 ouro, ilimitada (histórico) | Não | hibrido | controlada | 0/20 |
| [comparacao_decks_sem_ultimate_loja](comparacao_decks_sem_ultimate_loja.json) | nenhuma | 30 ouro, ilimitada (histórico) | Não | hibrido | aquisicao_real | 0/20 |
| [comparacao_decks_sem_ultimate_loja](comparacao_decks_sem_ultimate_loja.json) | nenhuma | 30 ouro, ilimitada (histórico) | Não | somente_defesa | controlada | 0/20 |
| [comparacao_decks_sem_ultimate_loja](comparacao_decks_sem_ultimate_loja.json) | nenhuma | 30 ouro, ilimitada (histórico) | Não | somente_defesa | aquisicao_real | 0/20 |

## Chefes isolados com vida cheia

O personagem reinicia com 60 HP em cada caso: essa tabela não mede desgaste entre encontros. Alvar/Tekks inclui as duas fases no mesmo combate.

| Ultimate | Deck | Chefe/território | Vitórias/casos |
|---|---|---|---:|
| mana_ancestral | dano_efeitos | 1 | 20/20 |
| mana_ancestral | dano_efeitos | 2 | 1/20 |
| mana_ancestral | dano_efeitos | 3 | 0/20 |
| mana_ancestral | dano_efeitos | 4 | 0/20 |
| mana_ancestral | dano_efeitos | 5 | 0/20 |
| mana_ancestral | dano_efeitos | 6 | 0/20 |
| mana_ancestral | dano_efeitos | 7 | 0/20 |
| mana_ancestral | hibrido_efeitos | 1 | 20/20 |
| mana_ancestral | hibrido_efeitos | 2 | 19/20 |
| mana_ancestral | hibrido_efeitos | 3 | 7/20 |
| mana_ancestral | hibrido_efeitos | 4 | 9/20 |
| mana_ancestral | hibrido_efeitos | 5 | 14/20 |
| mana_ancestral | hibrido_efeitos | 6 | 1/20 |
| mana_ancestral | hibrido_efeitos | 7 | 0/20 |
| rugido_da_floresta | dano_efeitos | 1 | 20/20 |
| rugido_da_floresta | dano_efeitos | 2 | 1/20 |
| rugido_da_floresta | dano_efeitos | 3 | 0/20 |
| rugido_da_floresta | dano_efeitos | 4 | 0/20 |
| rugido_da_floresta | dano_efeitos | 5 | 0/20 |
| rugido_da_floresta | dano_efeitos | 6 | 0/20 |
| rugido_da_floresta | dano_efeitos | 7 | 0/20 |
| rugido_da_floresta | hibrido_efeitos | 1 | 20/20 |
| rugido_da_floresta | hibrido_efeitos | 2 | 19/20 |
| rugido_da_floresta | hibrido_efeitos | 3 | 7/20 |
| rugido_da_floresta | hibrido_efeitos | 4 | 8/20 |
| rugido_da_floresta | hibrido_efeitos | 5 | 16/20 |
| rugido_da_floresta | hibrido_efeitos | 6 | 1/20 |
| rugido_da_floresta | hibrido_efeitos | 7 | 0/20 |
| nenhuma | dano_efeitos | 1 | 20/20 |
| nenhuma | dano_efeitos | 2 | 0/20 |
| nenhuma | dano_efeitos | 3 | 0/20 |
| nenhuma | dano_efeitos | 4 | 0/20 |
| nenhuma | dano_efeitos | 5 | 0/20 |
| nenhuma | dano_efeitos | 6 | 0/20 |
| nenhuma | dano_efeitos | 7 | 0/20 |
| nenhuma | hibrido_efeitos | 1 | 20/20 |
| nenhuma | hibrido_efeitos | 2 | 19/20 |
| nenhuma | hibrido_efeitos | 3 | 6/20 |
| nenhuma | hibrido_efeitos | 4 | 4/20 |
| nenhuma | hibrido_efeitos | 5 | 8/20 |
| nenhuma | hibrido_efeitos | 6 | 0/20 |
| nenhuma | hibrido_efeitos | 7 | 0/20 |
| mana_ancestral | somente_dano | 1 | 20/20 |
| mana_ancestral | somente_dano | 2 | 14/20 |
| mana_ancestral | somente_dano | 3 | 4/20 |
| mana_ancestral | somente_dano | 4 | 0/20 |
| mana_ancestral | somente_dano | 5 | 0/20 |
| mana_ancestral | somente_dano | 6 | 0/20 |
| mana_ancestral | somente_dano | 7 | 0/20 |
| mana_ancestral | hibrido | 1 | 20/20 |
| mana_ancestral | hibrido | 2 | 20/20 |
| mana_ancestral | hibrido | 3 | 18/20 |
| mana_ancestral | hibrido | 4 | 20/20 |
| mana_ancestral | hibrido | 5 | 20/20 |
| mana_ancestral | hibrido | 6 | 18/20 |
| mana_ancestral | hibrido | 7 | 1/20 |
| mana_ancestral | somente_defesa | 1 | 0/20 |
| mana_ancestral | somente_defesa | 2 | 0/20 |
| mana_ancestral | somente_defesa | 3 | 0/20 |
| mana_ancestral | somente_defesa | 4 | 0/20 |
| mana_ancestral | somente_defesa | 5 | 0/20 |
| mana_ancestral | somente_defesa | 6 | 0/20 |
| mana_ancestral | somente_defesa | 7 | 0/20 |
| rugido_da_floresta | somente_dano | 1 | 20/20 |
| rugido_da_floresta | somente_dano | 2 | 14/20 |
| rugido_da_floresta | somente_dano | 3 | 4/20 |
| rugido_da_floresta | somente_dano | 4 | 0/20 |
| rugido_da_floresta | somente_dano | 5 | 0/20 |
| rugido_da_floresta | somente_dano | 6 | 0/20 |
| rugido_da_floresta | somente_dano | 7 | 0/20 |
| rugido_da_floresta | hibrido | 1 | 20/20 |
| rugido_da_floresta | hibrido | 2 | 20/20 |
| rugido_da_floresta | hibrido | 3 | 18/20 |
| rugido_da_floresta | hibrido | 4 | 19/20 |
| rugido_da_floresta | hibrido | 5 | 14/20 |
| rugido_da_floresta | hibrido | 6 | 19/20 |
| rugido_da_floresta | hibrido | 7 | 0/20 |
| rugido_da_floresta | somente_defesa | 1 | 20/20 |
| rugido_da_floresta | somente_defesa | 2 | 20/20 |
| rugido_da_floresta | somente_defesa | 3 | 16/20 |
| rugido_da_floresta | somente_defesa | 4 | 20/20 |
| rugido_da_floresta | somente_defesa | 5 | 20/20 |
| rugido_da_floresta | somente_defesa | 6 | 20/20 |
| rugido_da_floresta | somente_defesa | 7 | 2/20 |
| nenhuma | somente_dano | 1 | 20/20 |
| nenhuma | somente_dano | 2 | 14/20 |
| nenhuma | somente_dano | 3 | 4/20 |
| nenhuma | somente_dano | 4 | 0/20 |
| nenhuma | somente_dano | 5 | 0/20 |
| nenhuma | somente_dano | 6 | 0/20 |
| nenhuma | somente_dano | 7 | 0/20 |
| nenhuma | hibrido | 1 | 20/20 |
| nenhuma | hibrido | 2 | 20/20 |
| nenhuma | hibrido | 3 | 16/20 |
| nenhuma | hibrido | 4 | 16/20 |
| nenhuma | hibrido | 5 | 0/20 |
| nenhuma | hibrido | 6 | 18/20 |
| nenhuma | hibrido | 7 | 0/20 |
| nenhuma | somente_defesa | 1 | 0/20 |
| nenhuma | somente_defesa | 2 | 0/20 |
| nenhuma | somente_defesa | 3 | 0/20 |
| nenhuma | somente_defesa | 4 | 0/20 |
| nenhuma | somente_defesa | 5 | 0/20 |
| nenhuma | somente_defesa | 6 | 0/20 |
| nenhuma | somente_defesa | 7 | 0/20 |

## Limites de interpretação

- Defesa pura sem Ultimate ofensiva não tem via de dano nas regras da versão medida. `sem_via_de_dano` é uma impossibilidade estrutural dessa composição, não uma derrota simulada.
- Com Rugido, um deck de defesa pode matar, mas o dano vem da Ultimate. Mana Ancestral não causa dano diretamente; Forças Ancestrais também precisaria de um ataque para aproveitar sua Força.
- Vitórias com cura da loja demonstram ausência de carta de cura, não ausência de recuperação de vida.
- Uma composição não representa toda a família de estratégias. Foram incluídas variações de dano direto e de ataques com Veneno/Sangramento para reduzir essa limitação.
- Busca curta, compras predefinidas, composições/planos LV2 fixos e limite de turnos restringem o bot. Falhar aqui não prova que pessoas não possam vencer. As políticas podem divergir em sorteios e economia.
- Não usar uma vitória com deck já pronto como prova de que a mesma composição é obtida cedo e vence na progressão real.

Total registrado: **2040 tentativas de campanha** e **2100 casos de chefes isolados**. Tentativas interrompidas e provas sem via de dano não são campanhas jogadas até o fim.
