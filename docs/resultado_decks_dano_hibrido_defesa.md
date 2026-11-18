# Resultado: dano, híbrido e defesa sem cartas de cura

> Histórico com cura da loja ilimitada a 30 ouro. O usuário aprovou depois três compras por run a 30/45/60; as taxas abaixo não validam essa revisão. Os relatórios `comparacao_decks_cura_limitada_*.json` e a tabela consolidada separam a regra nova.

**Cartas de cura não são obrigatórias nas regras atuais.** O bot completou campanhas com um híbrido de dano/defesa/limpeza e com uma construção defensiva apoiada em Ultimate ofensiva. Essas vitórias usam recuperação comprada com ouro entre encontros e a cura normal pós-chefe; não demonstram vitória sem qualquer recuperação de vida.

Nenhum valor ou regra do jogo foi alterado para obter os resultados. Não foram usados saves reais, invulnerabilidade ou melhorias permanentes. Todos começam com 60 HP e energia 2. Dez testes específicos das ferramentas estão aprovados; consolidação incremental de regressão: 649 testes em 68 módulos.

## Exemplos principais

| Composição de nove cópias | Ultimate | Campanha com deck pronto desde o início | Campanha com aquisição real |
|---|---|---:|---:|
| Só dano direto: 3 Socos, 3 Arcos, 3 Lanças | Mana Ancestral | 0/10 | 0/10 |
| Só ataques com efeitos: 3 Socos, 3 Adagas, 3 Zarabatanas | Mana Ancestral | 0/10 | 0/10 |
| Híbrido simples: 2 Socos, 2 Arcos, 3 Protetoras, 2 Esferas Escudo | Mana Ancestral | 0/10 | 1/10 |
| Híbrido com limpeza: 3 Arcos, 3 Protetoras, 2 Esferas Escudo, 1 Purificadora | Mana Ancestral | 6/10 | 5/10 |
| Defesa com limpeza: 3 Protetoras, 3 Esferas Escudo, 2 Totens, 1 Purificadora | Rugido da Floresta | 7/10 | 8/10 |

Condições dessa tabela: cura da loja habilitada e paga com ouro, até três LV2, zero melhorias permanentes. São cinco sementes com duas políticas do bot (conservadora/agressiva), **não dez sementes independentes**. Limite de 40 turnos por combate. Purificadora permanece LV1, portanto limpa negativos e **não cura**. Não há Poção de Cura ou Máscara nos decks.

Planos LV2: dano direto evolui três Arcos; dano por efeitos, três Adagas; híbrido simples, dois Arcos e uma Protetora; híbrido com limpeza, três Arcos; defesa, três Esferas Escudo. No controle, o deck completo e essas evoluções estão prontos desde o começo: é uma condição artificial para isolar a capacidade de combate. Na aquisição real, tipos, materiais e evoluções precisam ser obtidos/pagos normalmente.

A campanha real sempre começa com o deck obrigatório de três Socos e três Protetoras. Por isso, “defesa” e “só dano” descrevem o deck montado depois das aquisições, não todos os encontros desde o tutorial. Cada encontro registra `restricao_atendida`, composição e LV2 efetivamente equipados. A coluna de deck pronto é a que testa a restrição desde o primeiro confronto.

Fontes: [Mana com LV2 e loja](comparacao_decks_lv2_mana_loja.json), [Rugido com LV2 e loja](comparacao_decks_lv2_rugido_loja.json).

## Como interpretar

1. **Dano puro:** as duas composições testadas não completaram. Isso indica dificuldade dessas construções e políticas; não prova impossibilidade de todos os decks ofensivos ou de uma pessoa vencer. A versão de golpes diretos já sofre contra Sangramento e chefes intermediários; a versão de efeitos também não resolveu a campanha nessa amostra.
2. **Híbrido:** pode completar sem carta de cura. Limpeza, concentração de dano, compra de recuperação entre lutas e evoluções ajudam a compor uma rota viável. A versão com limpeza também muda a quantidade de Arcos/Socos e os alvos de evolução: não atribuir toda a diferença apenas à Purificadora.
3. **Defesa pura:** Escudo, Totem e limpeza não retiram vida inimiga. Sem fonte ofensiva adicional, não existe condição de vitória para essa composição. Com Rugido, ela ganha uma condição de vitória: carregar e repetir a Ultimate. O dano vem do Rugido, não da defesa. Forças Ancestrais aumenta Força, mas ainda precisaria de ataques para causar dano; Mana também não causa dano diretamente.
4. **Sustentação:** nenhum dos decks LV1 da primeira matriz completou sem cura da loja. É um sinal de desgaste entre encontros. Nos controles de LV2 com loja, o híbrido com limpeza venceu inclusive 4/10 sem usar Ultimate, mas 0/10 na aquisição real sem Ultimate. Ter uma composição final viável não garante obtê-la cedo e atravessar a economia da run.

## Escopo da comparação

Foram comparadas sete composições das três famílias: dano direto, dano por efeitos, híbrido simples, híbrido com efeitos, híbrido com limpeza, defesa com Escudo/Totem e defesa com limpeza. Todas têm nove cópias e respeitam três por tipo.

A primeira matriz usa dez sementes por política e LV1, com/sem cura da loja, sem Ultimate/com Mana/com Rugido. Também enfrenta os sete chefes isoladamente com HP cheio para separar capacidade de combate do desgaste. O controle LV2 usa cinco sementes por política, até três evoluções e cura paga na loja.

[Tabelas completas e relatórios brutos](comparacao_decks_sem_cura.md). A busca do bot é curta, usa planos fixos de compra/evolução e não explora todas as combinações das vinte cartas. A amostra não estima taxas de vitória de jogadores humanos, nem valida o balanceamento final. Nenhuma campanha humana foi jogada nesta verificação.

Conclusão para o projeto: substituir a afirmação ampla de que “só defesa/cura vence” por **“há rotas sem cartas de cura, mas a recuperação entre encontros e as ferramentas de resposta aos efeitos continuam relevantes; dano puro ainda não foi validado pelas composições testadas”**. Preservar o sistema e testar escolhas ofensivas mais a fundo antes de alterar os números novamente.
