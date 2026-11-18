# Diagnóstico e proposta roguelite — avaliação

> Registro da fase de diagnóstico. Após esta entrega, o usuário autorizou continuar com a implementação. O estado implementado e seus limites estão em [implementacao_balanceamento_roguelite.md](implementacao_balanceamento_roguelite.md); as referências abaixo a “nenhuma mudança” e “aguarda avaliação” descrevem a entrega original, não o estado atual da branch.

17/11/2026. **Nenhuma mudança de regra implementada. Todos os valores propostos aguardam avaliação.** Leitura integral de AGENTS.md e do documento externo ORIENTACOES_CODEX_ROGUELITE.md. Os oito itens abaixo separam fatos observados de propostas experimentais; não representam campanha jogada ou balanceamento validado.

## 1. Base e fluxos reais

Clone usado: `C:\Users\marco\OneDrive\Desktop\Scape-from-stone-de-cut-git`. Após `git fetch origin main`, main e origin/main estavam em `ad593a5`, divergência 0/0. Status inicial vazio, sem alterações locais apresentadas pelo Git; saves e demais ignorados preservados. Branch criada: `feature/balanceamento-roguelite`. Sem commit, push ou merge.

| Área | Código e diagnóstico |
|---|---|
| Entrada | `main.py`: eventos de janela antes da cena; chama save na saída. Menu → seleção → tutorial → mapa → batalha. |
| Cartas | `card_definitions.CARD_SPECS`, `card_catalog.AVAILABLE_CARD_POOL`: 20 disponíveis, outras 75 bloqueadas. |
| Deck | `deck_loadout.add_card_to_slots()/commit_deck()`: 6 a 18 espaços preenchidos, até três por tipo. Desbloquear tipo permite equipar três cópias sem comprá-las individualmente. |
| Recompensa | `CombatEngine.generate_rewards()/choose_reward()`: até três tipos ausentes, escolher um ou pular. `SaveManager.update_from_game()` coloca aquisição na coleção; equipar na Mochila. |
| Loja | `shop_system.purchase_card()` recusa tipo já possuído. Não existem materiais nem níveis. |
| Combate | `start_combat()/_begin_player_turn()`: energia 2, +1/turno até 8, mão 3/4/5, cartas não usadas permanecem. Ultimate começa com carga zero. |
| Chefes | `choose_next_action()` planeja duas ações antes da vez do jogador. Especial em cada oitavo ato; normalmente segunda ação da quarta rodada. Não há resposta entre duas ações inimigas. |
| Morte | `_game_over()` não encerra run no save; `BattleScene._save_progress()` ignora game_over; R recarrega checkpoint. `apply_to_game()` transforma HP zero em vida máxima. |
| Continuação | `resume_from_save()` reinicia inimigo, turno e pilhas; pode usar HP atual gravado ao sair. Mistura estado intermediário do jogador com início do encontro. |
| Vitória | `finish_map_phase()` e `campaign_progress.record_*()` gravam progresso. Cura pós-chefe de 30% da vida máxima; Tekks é fase do mesmo combate, sem prêmio intermediário. |

Conclusão: há campanha/deckbuilding, mas faltam perfil/run separados e inventário individual. Não basta ajustar dano.

## 2. Tabela das 20 cartas N1 atuais

Fontes: `card_definitions.py:CARD_SPECS`, `TacticalCardEffect.apply()`, `Combatant` em `entity.py`, `shop_system.CARD_PRICES`.

E = energia; D = dano imediato; S = Escudo; V = vida recuperada; A = Força + bônus temporários + Aura. Ataques recebem A uma vez por carta, inclusive dardos. Vulnerável aumenta ataques em 25%, arredondados para cima; não aumenta periódicos. Todas as 20 estão disponíveis na loja e no pool de recompensa; recompensa só oferece tipo ausente, loja recusa tipo já possuído. Soco/Protetora começam com três cópias cada.

| Carta | E | D imediato | Periódico / efeito, duração, condição | Ouro atual |
|---|---:|---|---|---:|
| Esfera Protetora | 1 | — | 10 S por 2 inícios de turno do dono | 40 |
| Soco Simples | 1 | 6+A | Sem adicional | 40 |
| Investida | 2 | 10+A | Corpo a corpo não tem benefício mecânico extra | 55 |
| Aura Rubra | 3 | — | +8 A por 3 turnos próprios; renova sem somar | 70 |
| Poção Fragilizante | 3 | — | Vulnerável por 3 turnos do alvo | 70 |
| Poção Purificadora | 3 | — | Remove negativos próprios imediatamente, sem cura | 70 |
| Totem Protetor | 5 | — | Ignora próximo ataque inteiro e seus efeitos; não expira por turno, não acumula, não impede periódicos já ativos | 100 |
| Zarabatana Venenosa | 3 | 10+A em 3 dardos | 2 Veneno/2 turnos: até 20 direto isolados. Totem barra aplicação | 70 |
| Disparo de Arco | 2 | 20+A | Sem adicional | 55 |
| Esfera Escudo | 4 | — | 30 S por 2 inícios de turno do dono | 85 |
| Machado Quebra-Escudo | 5 | — | Zera S inimigo, sem ataque nem A | 100 |
| Amuleto Dissipador | 4 | — | Remove todos os estados, S e Força inimigos; também remove seus debuffs aplicados no alvo | 85 |
| Adaga Sangrenta | 3 | 5+A | 2 Sangramento/2 turnos: 6 direto por ação ofensiva do afetado que tire vida, até 2 gatilhos/turno | 70 |
| Máscara Ancestral | 6 | — | 20 V + 20 S; S dura 2 inícios de turno | 115 |
| Machados Gêmeos | 4 | 40+A | Um ataque mecânico; não dobra A | 85 |
| Lança Perfurante | 3 | 30+A | Não ignora S | 70 |
| Bola de Fogo | 4 | 10+A | Fogo 1 por 3 turnos: até 9 adicionais contra S primeiro; reaplicar soma intensidade até 3 e renova duração | 85 |
| Poção de Cura | 3 | — | 20 V imediatos, limitada ao máximo; vida recuperada persiste entre encontros | 70 |
| Surto de Energia | 2 | — | +2 E no próximo turno, teto total 8; não aumenta máximo | 55 |
| Poção Venenosa | 4 | — | 2 Veneno/2 turnos: até 20 direto isolados; não recebe A nem consome Totem | 85 |

Condições comuns: cura falha sob bloqueio de cura e limita à vida faltante; S falha se houver bloqueio de Escudo. Escudo acumula em camadas consumíveis, não se reaplica por dois turnos. Aura já perde um turno ao encerrar o turno da aplicação.

Veneno acumula até 5 stacks, renova 2 turnos mesmo no teto e ignora S. Não somar 20 por carta sem considerar sobreposição. Sangramento pune quem ataca: ataque absorvido inteiramente não ativa, multigolpe conta uma ação. Dois stacks podem causar até 24 isolados em dois turnos com duas ações válidas cada, mas zero se o afetado só defender/curar. Esses efeitos não são equivalentes a dano garantido.

## 3. Comparação de utilidade e propostas N1 e N2

Investida tem metade do dano do Arco pelo mesmo custo sem vantagem mecânica. Três Protetoras dão 30 S por 3 E, mas exigem três cartas; Esfera Escudo concentra o efeito por 4 E. Machado é mais caro que Amuleto, embora preserve debuffs. Zarabatana combina dano e Veneno; Poção Venenosa tem nicho contra Totem, portanto não declarar inferioridade universal. Fogo isolado entrega 19 bloqueáveis distribuídos por 4 E contra 40 imediatos de Machados. Surto só transfere energia atualmente e pode ser inútil no teto.

Retenção da mão torna carta cara um obstáculo à compra; concentração de efeito por carta também tem valor. Cura entre encontros, prevenção de debuff com Totem, dispel e sustentação precisam pesar na economia. Curas recicláveis em deck curto podem incentivar prolongar combates fáceis; medir antes de inventar limite.

**Proposta N1:** preservar regras globais de status, energia, mão e Ultimate; mudar apenas valores/custos específicos abaixo. Ouro compra desbloqueio de tipo, não material. Primeiro avaliar N1; N2 depende dessa base.

| Carta | N1 proposto: E; efeito | Ouro por tipo | N2 proposto: mesmo E; efeito | Ouro para evoluir |
|---|---|---:|---|---:|
| Soco Simples | 1; 6 D | 30 | 9 D | 40 |
| Esfera Protetora | 1; 10 S | 35 | 14 S | 40 |
| Investida | 2; 18 D | 40 | 24 D | 45 |
| Disparo de Arco | 2; 20 D | 55 | 26 D | 55 |
| Lança Perfurante | 3; 30 D | 65 | 38 D | 60 |
| Machados Gêmeos | 4; 40 D | 85 | 50 D | 70 |
| Aura Rubra | 2; +6 A por 3 turnos | 65 | +8 A por 3 turnos | 65 |
| Poção Fragilizante | 1; Vulnerável por 3 turnos | 45 | Mesmo Vulnerável +5 S próprios | 50 |
| Poção Purificadora | 1; limpar negativos | 45 | Limpeza +6 V | 50 |
| Totem Protetor | 3; um Totem | 75 | Um Totem +8 S | 65 |
| Zarabatana Venenosa | 3; 10 D +2 Veneno | 75 | 16 D + mesmos 2 Veneno | 65 |
| Poção Venenosa | 2; 2 Veneno | 50 | Mesmos 2 Veneno +6 S | 55 |
| Adaga Sangrenta | 2; 8 D +2 Sangramento | 60 | 14 D + mesmos 2 Sangramento | 55 |
| Bola de Fogo | 2; 12 D +Fogo 1/3 turnos | 55 | 18 D +mesmo Fogo | 55 |
| Esfera Escudo | 3; 32 S | 65 | 42 S | 60 |
| Machado Quebra-Escudo | 1; zerar S | 35 | Zerar S +8 S próprios, sem ataque | 40 |
| Amuleto Dissipador | 2; dissipar como hoje | 60 | Dissipar +8 S próprios | 55 |
| Poção de Cura | 3; 20 V | 75 | 26 V | 65 |
| Máscara Ancestral | 4; 18 V +22 S | 90 | 24 V +28 S | 75 |
| Surto de Energia | 1; +2 E próximo turno, teto 8 | 40 | +3 E próximo turno, teto 8 | 45 |

N1 barateia respostas de limpeza, quebra de S e preparo, sem mudar suas regras; cura recebe preço pela sustentabilidade, não pelo custo de uso. Investida fica ligeiramente abaixo do Arco em dano, mas custa 15 ouro menos para obter; se continuar sempre descartada, testar dano 20 antes de inventar habilidade de movimento. Esfera Escudo ganha eficiência e concentração, mantendo necessidade de esperar 3 E. Máscara troca pico tardio por uso mais cedo.

N2 não usa multiplicador universal. Cada compra consome três materiais extras do mesmo tipo mais ouro e melhora uma instância. Híbridos propostos exigem parâmetros novos no efeito; não estão disponíveis hoje. Não elevar stacks por aplicação acima de 2, percentual de Vulnerável ou limites globais. Durações não indicadas permanecem as do N1. Textos e valores impressos devem acompanhar uma futura aprovação, preservando originais de arte.

## 4. Economia atual e orçamento proposto das 21 batalhas

`CombatEngine._on_enemy_defeated()` concede 30–50 ouro por comum e 50–70 por chefe, uniformes inteiros, somente primeira vitória. São 14 comuns +7 chefes; tutorial é adicional às 21 e concede 30 uma vez (`TutorialScene._complete_tutorial()`). Tekks não dá prêmio de fase. Revanches não dão ouro nem cartas (`is_replay`); cura pós-chefe pode persistir em revanche e exige teste contra exploração.

| Território / vitórias | Atual: intervalo e média do trecho | Média acumulada sem tutorial | Proposta fixa: comum + comum + chefe | Proposta acumulada sem saldo inicial |
|---|---|---:|---|---:|
| T1 / 1–3 | 110–170; média 140 | 140 | 35+35+60 =130 | 130 |
| T2 / 4–6 | 110–170; média 140 | 280 | 40+40+65 =145 | 275 |
| T3 / 7–9 | 110–170; média 140 | 420 | 40+40+70 =150 | 425 |
| T4 / 10–12 | 110–170; média 140 | 560 | 45+45+75 =165 | 590 |
| T5 / 13–15 | 110–170; média 140 | 700 | 45+45+80 =170 | 760 |
| T6 / 16–18 | 110–170; média 140 | 840 | 50+50+85 =185 | 945 |
| T7 / 19–21 | 110–170; média 140 | 980 | 50+50+100 =200 | 1.145 |

Atual total: 770–1.190, média 980; incluindo tutorial: 800–1.220, média 1.010. Não há renda por golpe ou por turno. Todos os 18 tipos não iniciais custam 1.395 na loja atual, mas aceitar um tipo novo em cada vitória completa a coleção na 18ª, sem gastar. Compras antecipam acesso; recompensas gratuitas não são ouro adicional.

Proposta: ouro fixo acima, para reduzir variância econômica durante calibração. Toda nova run inicia com 30 ouro. Na primeira, os 30 do tutorial correspondem a esse saldo, não somam outro bônus; próximas runs recebem 30 sem repetir tutorial. Sem prêmio de revanches, incluindo materiais/fragmentos. Recomendar revanche como treino que restaura estado da run ao sair, sem cura persistente: mudança de fluxo para avaliação.

Manter inicialmente a compra temporária de +15 vida máxima por 50, limite três/run, sem cura imediata; perde na morte. Cura pós-chefe continua 30% (18 na base 60). Não confundir isso com melhoria permanente de +5 nem pressupor máximo temporário 105 na curva de dano.

Orçamento proposto de campanha completa: 30+1.145=1.175; vida temporária 150; três evoluções médias de 60=180; nove materiais comprados por 15=135; seis tipos médios de 60=360; sobra 350. Materiais gratuitos podem substituir compras. Antes de enfrentar Zanzara há 1.075 de renda potencial incluindo saldo inicial; os 100 da vitória final não ajudam a vencê-lo. Exemplo demonstra capacidade financeira, não aquisição ideal ou taxa de vitória.

## 5. Chefes, intenções e janelas de resposta

Fontes: `enemy_factory.create_point_enemy()/create_*()/_configure_boss()/choose_next_action()`, `CombatEngine.enemy_turn()/finish_enemy_turn()`, `Action.execute()`, `ForestSmokeEffect`, `CrimsonVigorEffect`. Valores nos níveis territoriais reais. Todos fazem duas ações/rodada, com escolhas por peso e orçamento; podem repetir ação. Especial substitui cada oitavo ato.

| Chefe | HP atual | Ações comuns atuais (peso) | Especial atual |
|---|---:|---|---|
| Octav | 78 | garras7 (55%), S8 (30%), cura8 (15%) | 14 |
| Alvar / Tekks | 76+44 | fase1: dano9 (45%), dano7 (35%), cura10 e +3 A/2 turnos (20%); fase2: 7 (40%), 9 (35%), 6 (25%) | 15 /13; contador reinicia na fase2 |
| Jozephino | 104 | 11 (35%), 13+Choque1 (30%), 12+Veneno2 (20%), S11 (15%) | 20+Choque2 |
| Sir Thomas | 116 | 9+Sangramento2 (35%), 11 (25%), 14 (25%), S10 (15%) | 21 |
| Jan-Pietro | 125 | 9+Sangramento2 (55%), 12+Sangramento2 (30%), S10+cura20 (15%) | 19 |
| Labrro | 146 | 13 (45%), 17 (35%), ambos ligam +4 A/2 turnos após bater; cura14 +mesma aura (20%) | 24+mesma aura |
| Zanzara | 190 | Foice20 (40%) e Passo24 (35%), ambos Sangramento2+Veneno1; Grilhões20+Vulnerável/2 turnos (25%) | 45+Veneno2 |

Problemas concretos, exemplos analíticos sem defesa ou recuperação:

- Duas Foices iniciais: 40 de dano, 4 Sangramento e 2 Veneno. Atacar duas vezes depois retirando vida provoca 24 de Sangramento e encerrar turno custa 10 Veneno. Pode matar herói de 60 antes da segunda rodada inimiga.
- Grilhões seguido de Passo: 20+30=50 pela Vulnerabilidade recém-aplicada. Foice seguida de Travessia soma 65 antes dos efeitos. Totem atual custa 5 e não é jogável com os 2 iniciais; S não evita a aplicação de debuff se não houver Totem.
- Labrro pode causar 13 com Corte e ligar aura para Varredura de 21 na mesma rodada. A aura renova, não soma infinitamente.
- Jan-Pietro pode repetir postura: até 40 cura e 20 S numa rodada, enquanto Sangramento pune acelerar o ataque.
- Jozephino pode acumular Choque de duas ações e restringir ainda mais uma mão retida. Avaliar energia e compra junto do dano.

**Proposta experimental:** manter pesos, duas ações, frequência de especiais, identidade e arte dos kits. Alterações específicas abaixo, sem exigir melhorias permanentes.

| Chefe | HP proposto | Valores propostos / janela |
|---|---:|---|
| Octav | 78 | Manter 7/S8/cura8/especial14; sentinela do ganho das cartas N1 |
| Alvar/Tekks | 76+44 | Manter valores; preservar estado do jogador na fase2 |
| Jozephino | 100 | Chave10; descarga11+Choque1; tóxico10+Veneno1; S11; especial18+Choque2. Limpeza N1 de 1 E oferece resposta |
| Sir Thomas | 116 | Manter kit; Totem N1 torna-se acessível no turno2 |
| Jan-Pietro | 125 | Cortes9/12 com 1 Sangramento cada; postura S10+cura10; especial19. Reduz sustentação e punição por agir |
| Labrro | 140 | Corte11; varredura14; cura10; aura+3/2 turnos nas mesmas ações; especial21+aura. Dupla ofensiva com buff prévio até31 |
| Zanzara | 175 | Foice12+Sangramento1; Passo15+Veneno1; Grilhões10+Vulnerável/2 turnos; especial26+Veneno1. Separar funções de debuff |

Limite: Zanzara proposto ainda causa até 38 com dupla comum e Vulnerável ativo; Passo+especial pode chegar a 52 com Vulnerável prévio, mais periódicos. Abaixo de 60 não prova justiça: entrada real pode ter pouca vida. Medir resposta com S32 por 3 E, Totem por 3 E e limpeza por 1 E. Se persistir morte inevitável apesar de boa decisão, avaliar restrição de pares de ações depois; não incluí-la silenciosamente.

Comuns atuais por bioma têm HP: T1 23–27; T2 31–35; T3 37–48; T4 49–54; T5 43–47; T6 63–64; T7 57–66, uma ação por turno. Curva não estritamente crescente. Mago do Santuário aplica Fogo intensidade3 por 2 turnos: até18 além do golpe; ponto de teste, sem alteração automática aqui.

Ultimates permanecem: Mana Ancestral restaura energia até8, compra5, limpa negativos; Forças dá +12 A na luta e40 S; Rugido quebra S, causa60+A e Fraqueza. Com gasto completo 2+3+4+5+6, primeira carga20 pode chegar no quinto turno. Mão e decisões podem atrasar; não presumir Ultimate na abertura nem alterar regras finalizadas.

## 6. Aquisição, duplicatas, evolução e progressão permanente

Recomendação: manter três cópias equipáveis por desbloqueio, agora criadas como instâncias estáveis N1. Desequipar só altera localização. **Não gera material nem nova instância.** Alternativa de adquirir cada cópia individualmente exigiria recalcular toda esta economia; não misturar modelos.

Proposta de recompensa por primeira vitória comum: escolher uma opção entre até dois tipos novos sorteados e pacote de **um material de tipo possuído escolhido pelo jogador**. Chefe: até dois tipos novos ou pacote de **três materiais de um tipo possuído escolhido**. Se esgotar tipos, mostrar material direcionado ou pular. Sem compensação automática em ouro. Seleção de material oferece todos os tipos possuídos; não depende de sorte uniforme entre20.

Loja: material de qualquer tipo possuído por15 ouro, compra repetida permitida; limite de estoque9 por tipo. Recusar pacote/compra que exceda limite, antes de cobrar; não converter excedente automaticamente. Sem venda/conversão nesta versão. Materiais ficam fora dos18 espaços e não entram nas pilhas de combate. Desbloqueio de tipo dá três instâncias, zero materiais.

Primeira evolução possível antes de Octav: dois materiais de comuns, terceiro comprado por15, evolução de Soco por40; renda30+35+35=100, custo55. Sacrifica duas escolhas de tipo novo. Pacote do chefe permite evolução dirigida sem sorte. Três upgrades exigem nove materiais, possíveis até fim de T2 sacrificando variedade. Alvo de observação: primeira normalmente T2–T3, terceira T5–T7; se teto vier cedo demais com pouca escolha, ajustar distribuição antes de inflar preços.

Exemplo obrigatório: três Socos N1 equipados (`soco-a/b/c`), três Socos extras de material e ouro suficiente. Evoluir `soco-a` → um N2 e dois N1 continuam equipados, reserva zera, cobra ouro uma vez, contador da run+1. Não fundir três equipadas em uma; não melhorar todas. Retirar N2 não devolve limite. Distribuições3 iguais,2+1 ou1+1+1 válidas. Máximo três N2 comprados na run, não apenas três equipados. Sem N3/fusão em combate.

**Fragmentos propostos**, nome provisório: chefes1–7 dão 1/1/2/2/3/3/5, total17. Só primeira vitória daquele encontro na run; Tekks dá junto do fim do chefe2. Runs novas podem recompensar novamente; revanche não. Persistir junto da vitória confirmada independentemente da escolha de carta/material.

| Melhoria permanente proposta | Benefício | Fragmentos | Limite |
|---|---|---:|---|
| Vida I/II/III | +5 de vida inicial/máxima por nível | 3/5/8 | +15 total |
| Energia inicial | Começa cada luta com3 em vez de2, +1 por turno e teto8 preservados | 12 | Uma compra |
| Preparação I | Escolher um terceiro tipo inicial entre Investida/Arco/Purificadora, com3 instâncias N1 | 4 | Uma compra |
| Preparação II | Amplia opções com Lança/Esfera Escudo/Poção Venenosa; continua apenas um tipo extra | 6 adicionais | Exige I |

Total38 fragmentos para todas. Sem dano permanente, material/N2 permanente ou deck anterior. Tipo preparado entra no inventário e jogador decide equipar. Energia3 é salto de50% na abertura: validar por último, nunca usá-lo como requisito para vencer. Campanha base deve ser testada com zero melhorias permanentes.

## 7. Perfil/run, saves, morte, retomada e migração

Proposta técnica para implementação posterior:

- Schema13 se a base continuar em12: separar `perfil`, `run`, opções. Perfil **por slot**, para avaliação; nenhum compartilhamento global silencioso. Excluir slot apaga perfil/run e exige mensagem explícita sobre fragmentos e melhorias.
- Perfil: `profile_id`, fragmentos, melhorias, opções de preparação, tutorial/cutscenes/guia vistos, Ultimates desbloqueadas/equipada preferida, melhor território e campanhas concluídas. Preferências globais já existentes permanecem separadas.
- Run: `run_id`, estado ativa/morta/concluída, mapa/encontros, ouro, vida, compras temporárias, tipos desbloqueados, instâncias `{copy_id, card_id, level}`, espaços com IDs ou nulo, materiais por tipo, `upgrades_purchased`0–3, preparação escolhida e prêmios recebidos. IDs não são índices dos espaços. Contar N1+N2 conjuntamente no limite de três por tipo.
- Evolução valida antes de cobrar: alvo possuído N1, run ativa, ouro, três materiais do mesmo tipo, contador<3. Altera uma instância, debita tudo e incrementa contador numa transação atômica; falha de validação/I/O restaura estado integral. Identificador da operação impede repetição de clique. Evoluir cópia desequipada também consome limite.
- Prêmio com chave `(run_id, encounter_id)`: ouro, fragmentos, progresso e registro de recebimento juntos. Salvar resultado/pendência da escolha para impedir ressorteio e dupla confirmação. Regras creditam saldo; partículas só representam visualmente. Falha de gravação bloqueia avanço com tentativa de salvar, sem dar prêmio de novo.

Morte: gravar imediatamente estado morto e revisão antes de habilitar Nova run. R e botão de mouse criam outro run_id; nunca retomam confronto morto. Run nova limpa mapa, chefes, ouro, aquisições, duplicatas, evoluções e vida temporária. Inicia cheia em60+vida permanente, seis starters e preparação aprovada. Preserva perfil, não coleção/deck antigo. Falha ao salvar morte mantém tela de morte com tentativa de gravação; não oferecer Continuar vivo.

Retomada viva recomendada: snapshot lógico após ação concluída e transição estável. Guardar HP, camadas de S/duração, buffs/contadores, energia/turno/Ultimate, IDs nas pilhas, inimigo/fase/HP, plano de ações/índice/contador e estado aleatório. Fechar não mata; continuar restaura snapshot sem refazer mão/intenção. Animação pode reiniciar, consequência lógica não. Fora de combate retoma mapa. Alternativa menor, recomeçar ambos do estado de entrada da luta, admite repetição por saída e precisa de aprovação separada; não misturar HP atual com inimigo cheio como hoje.

Revisão e registro de encerramento impedem recuperação automática de backup anterior a morte confirmada. Gravação atômica e recuperação precisam preservar essa informação. Não prometer impedir rollback manual de arquivos locais; queda antes de concluir gravação garante apenas último estado confirmado, limite a documentar/testar.

Vitória final: gravar prêmio de Zanzara e conclusão uma vez, marcar run concluída, mostrar resumo/preparação/nova run. Histórico permanece; ouro/material/N2 não passam à próxima. Sem pós-campanha para farm automático.

Migração v12 proposta: backup antes de converter; flags/Ultimates no perfil do próprio slot; fragmentos/melhorias permanentes zero, sem prêmio retroativo inventado. Run viva herda mapa/encontros/ouro/vida/compras temporárias; cada tipo conhecido gera exatamente três instâncias N1; espaços antigos apontam para instâncias distintas; reserva/contador zero. Migrações v8 e nomes legados continuam. Campanha já concluída migra concluída. Save antigo não guarda morte, portanto não inferi-la. Sem snapshot antigo, informar retomada legada de encontro reiniciado usando HP legado uma vez, oferecendo nova run sem apagar perfil; não alegar restauração de turno. Rejeitar versão futura desconhecida sem sobrescrever.

Laboratório: perfil/run isolados, invulnerabilidade e recursos artificiais, sem alimentar fragmentos/histórico de slots normais. Permitir preparar N2 e simular morte para testes. Não confundir laboratório com evidência de balanceamento.

## 8. Validação, apresentação/áudio e avaliação pendente

Evidência desta análise: leitura estática dos documentos e fluxos citados; cálculos analíticos. Não houve campanha jogada, simulação de campanha ou revisão visual/sonora. Números históricos de testes no AGENTS.md não são resultados desta entrega.

Ambiente preparado a pedido do usuário: instalador oficial Python 3.12.10 com assinatura válida da Python Software Foundation; instalação por usuário sem mudar PATH nem substituir launcher. `.venv` criada (já ignorada pelo Git); dependências existentes instaladas via `requirements-dev.txt`: pygame 2.6.1, NumPy 2.5.5 e Pillow 13.0.0, sem alterar requirements. O contexto restrito não enxergou o interpretador externo; a execução com acesso à instalação confirmou funcionamento.

Baseline executado com drivers SDL de vídeo/áudio dummy: `.venv\Scripts\python.exe -B -m unittest tests.test_tactical_cards tests.test_shop_and_combat_reset tests.test_life_recovery_after_combat tests.test_deck_slots -q`. **52 testes aprovados em 12,456 segundos**. Isso verifica a base existente, não as regras propostas, que não foram implementadas. Suíte completa não executada nesta etapa documental. `git diff --check` sem erros; status final apresenta apenas este documento novo entre os arquivos não ignorados.

Plano após aprovação:

1. Testar perfil/run, morte e transações: reset exato, persistência de fragmentos, isolamento de slots, falha de I/O sem cobrança parcial, cliques repetidos e recarga sem duplicação.
2. Verificar N1 antes de N2; três materiais e ouro exatos; caso dos três Socos; níveis mistos; limites por tipo/run; desequipar não libera quarto upgrade; edição não multiplica cópias; materiais fora do deck. Asserções sobre HP/estado/saldo observáveis.
3. Saves v8/v12/nomes legados, snapshot de Tekks, mão/intenção inalteradas na retomada, morte seguida de fechar/abrir, prêmio pendente, conclusão, recuperação de corrupção e laboratório. Usar diretórios temporários, sem saves reais.
4. Regressão dirigida: `test_tactical_cards`, `test_shop_and_combat_reset`, `test_life_recovery_after_combat`, `test_deck_slots`, `test_deck_clear_and_minimum`, `test_save_system`, `test_save_integration`, `test_test_save`, `test_tutorial_save_flow`, `test_territory_map`, `test_route_boss_and_backpack`, `test_mata_sombria_boss`, `test_swamp_boss`. Depois consolidar uma vez com `devtools/validate_isolated_tests.py`, conforme limites de memória.
5. Futuras simulações com sementes fixas e estratégias de dano/Aura, defesa/cura e Veneno/Sangramento; separar N1, até três N2 e perfil máximo. Medir vitória, turnos, HP, ouro, evolução por território e mortes sem resposta. Política automática fraca não prova impossibilidade. Demonstrar runs completas com zero melhorias permanentes e diferentes estratégias; nenhum item permanente pode ser requisito oculto.
6. Playtest humano da campanha base e chefes finais. Observar comuns3–6 turnos e chefes5–9 (dupla pode exceder) como faixas experimentais, não resultados. Medir se cura, deck de seis ou Totem se tornam solução única.

Apresentação/áudio é frente separada: preservar sprites, retratos, músicas e efeitos aprovados. Não alterar filtros, colisões ou estilo indiscriminadamente. Na interface futura, mostrar N1/N2, cópia alvo, contador0/3 por run, três materiais+ouro e saldo permanente separado. Botões de mouse para todas as ações, textos pt-BR, conferir janela1280×720/superfície1920×1080. Prévia antes de cobrar e feedback sem consumo na falha. Reutilizar sons existentes quando adequado; avaliar feedback de evolução sem gerar assets automaticamente. Conferir números impressos, intenções, impactos e eventos de compra/morte com avaliação humana; teste técnico não garante sincronismo ou qualidade perceptual.

**Aguardam avaliação:** tabela N1/preços e depois N2; ouro/saldo inicial/revanches; ajustes específicos de chefes; três instâncias por desbloqueio e materiais direcionados; fragmentos/melhorias e energia3; perfil por slot, migração e retomada fiel. Não iniciar implementação por aprovação presumida. Nenhuma alteração em regras, saves, assets ou testes faz parte desta entrega.
