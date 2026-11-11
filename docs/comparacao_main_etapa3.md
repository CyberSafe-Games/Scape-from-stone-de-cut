# Atualização da main na branch de áudio — 11/11/2026

Origem: `origin/main` em `ae383f5`; destino: `feature/audio-enemies`. A main compartilhada não foi alterada. O trabalho local aprovado foi preservado no commit `0b84b84` antes da integração.

## O que veio do grupo

| Área | Mudança recebida | Situação após conciliação |
| --- | --- | --- |
| Cartas | 75 cartas adicionais e regras de efeitos, totalizando 95 no catálogo | 20 cartas continuam jogáveis; as 75 novas estão indisponíveis enquanto faltam arte/animação. Não foram liberadas automaticamente. |
| Efeitos | Acúmulos de veneno, sangramento e queimadura; força temporária; imunidade; restrições de ataque, cura e bloqueio; Totens com gatilhos | Preservados. Gatilhos de Totem conciliados com os múltiplos debuffs de Zanzara. |
| Chefes | Não chegou sistema de baralho/mão/cartas para chefes | Continuam executando `Action` e intenções. Uso de cartas por chefes precisa de uma implementação específica se for confirmado pelo grupo. |
| Progressão | Rotas com dois encontros antes do chefe; migração dos contadores antigos; regras de liberação e revanche | Preservadas. |
| Recompensas | Sorteio apenas de cartas disponíveis ainda não obtidas, com tela de continuidade quando não houver novas recompensas | Preservado. |
| Cura | Recupera 30% da vida máxima somente após minibosses, sem ultrapassar o máximo | Preservada. |
| Mochila, loja e saves | Bloqueia compra, equipamento e uso das cartas indisponíveis; migra saves e mantém deck inicial válido | Preservado. Nenhum save do usuário foi alterado manualmente para teste. |
| Tipografia | Fonte autoral Igarapé Pixel e adaptação à apresentação Full HD | Preservada, junto do cenário final sombrio. |
| Animação | Mistura de poses, alinhamento, recuo de dano e recuperação de postura para jogador e inimigos | Preservada junto do kit, portal, barco e derrota de Zanzara. |
| Inimigos | Viniurgo na primeira região, com soco duplo e chute frontal | Preservado; áudio físico reaproveitado e coberto pelos testes. |
| Documentação e testes | README, guia AGENTS compartilhado, testes de cartas e dependências NumPy/Pillow | Preservados. As decisões de fluxo aprovadas pelo usuário foram acrescentadas ao guia compartilhado. |

## Conflitos efetivos e resolução

A comparação preliminar havia apontado oito arquivos potencialmente conflitantes. O merge real combinou seis automaticamente e deixou dois conflitos efetivos:

- `src/systems/combat_engine.py`: manter o disparo dos Totens novos e a aplicação dos múltiplos debuffs de Zanzara, respeitando bloqueio e proteção.
- `src/ui/entity_view.py`: manter os tempos e transições de recuperação novos, a reação de dano do jogador, a âncora usada pelo portal e o tempo dedicado de derrota de Zanzara.

Nenhum arquivo foi substituído integralmente pela versão de um dos lados. O `AGENTS.md` local anterior foi copiado para backup antes do merge; o guia compartilhado recebido foi preservado e complementado com as decisões aprovadas.

## Pontos para decidir depois

- Confirmar com o grupo a intenção de dar cartas aos chefes: isso não está implementado na main recebida. Não mudar a IA ou o balanceamento para presumir essa regra.
- As 75 cartas bloqueadas ainda precisam de arte, animação e definição dos sons antes de serem liberadas. A PR atual mantém esse bloqueio.
- A aprovação funcional anterior vale para os ajustes da etapa 3 realizados por nós. Mudanças recebidas e a conciliação são verificadas tecnicamente nesta atualização e podem ser avaliadas juntas no main.py.
- Publicação da PR ocorrerá depois da revisão desta lista, conforme combinado; nenhum merge na main foi autorizado.

## Ajustes de compatibilidade encontrados nos testes

- O teste dos doze efeitos genéricos de ultimate agora verifica explicitamente o fallback legado. Zanzara tem renderizador próprio aprovado e suprime esse efeito genérico para evitar sobreposição; as animações novas seguem cobertas por seus testes dedicados.
- O teste de áudio de Zanzara foi ajustado para importar o módulo auxiliar como pacote, funcionando tanto na execução isolada quanto na descoberta completa.
- A execução monolítica da suíte acumulou caches de sprites até causar falta de memória no ambiente. A validação foi reorganizada em processos isolados por módulo (`devtools/validate_isolated_tests.py`), sem janelas e com liberação de memória entre lotes. Não tratar a execução interrompida como aprovada; usar o resultado consolidado por módulo.

## Resultado final da integração

- 472 testes aprovados em 51 módulos executados isoladamente, sem abrir janelas. Os dois módulos com expectativas antigas foram ajustados e reexecutados; o relatório preserva o resultado inicial e o reteste aprovado.
- Auditoria dos 79 efeitos de áudio aprovada, sem exceder os limites individuais configurados.
- Novos testes confirmam que Totens de cura/veneno preservam seus gatilhos e bloqueiam corretamente os debuffs de Zanzara; sem proteção, Sangramento e Veneno continuam aplicados.
- O teste da âncora do portal foi atualizado para a posição dos pés produzida pelo renderizador novo da main (382, 627 no cenário de teste), preservando a exigência de ignorar margens transparentes.
- Registros: `docs/validacao_main_por_modulo.json` e `docs/audio_mix_audit.json`.

## Retrato e colisões — revisão após conferir a main

- Retrato de Zanzara corrigido para voltar ao rosto aprovado em `bosses/zanzara-necromante-v8.png`. O mapa de retratos emoldurados recebido da main estava sobrescrevendo essa escolha com `framed/zanzara.png`, uma imagem diferente. Os outros retratos permanecem no mapa emoldurado.
- As reações gerais de impacto (inclinação, compressão, tonalidade avermelhada e recuperação de postura) vieram da main, assim como FLASH_DURATION alterado de 220 para 560 ms.
- A reação de dano dedicada do Zanzara, feita no nosso kit, ainda divide o tempo por 220 ms; combinada ao valor global novo, isso segura o primeiro quadro e encurta a parte animada. Diagnóstico identificado para o próximo refinamento, sem alterar as animações nesta troca de retrato.

## Moldura do retrato de Zanzara

O rosto aprovado agora é composto dentro da mesma moldura do protagonista, com proporções e renderização iguais na HUD. A composição reutiliza a arte existente da borda e mantém intactos os PNGs originais. Três testes de retrato aprovados, incluindo comparação de pixels da moldura e conferência da fonte do rosto. Prévia: docs/retratos_moldura_compartilhada.png. Animações de colisão permanecem como diagnóstico pendente.

## Reação de dano de Zanzara — ajuste de compatibilidade

Após aprovação do rosto e moldura, a sequência de dano passou a usar FLASH_DURATION do jogo em vez do valor fixo de 220 ms. Os oito quadros existentes agora avançam por toda a janela atual de 560 ms, eliminando a espera artificial no primeiro quadro causada pela conciliação com a main. Nenhum sprite, escala, golpe ou efeito de áudio foi recriado. Foram aprovados 27 testes direcionados, incluindo uma regressão que verifica a passagem pelos oito quadros. A avaliação perceptual fica com o usuário no piloto: H para receber um golpe; 1–4 para atacar.

## Aprovação e preparação para publicação

O usuário aprovou os refinamentos de rosto, moldura e reação de dano no piloto. A reação dedicada de Zanzara agora acompanha FLASH_DURATION global, preservando a arte. A publicação da PR foi autorizada após essa revisão; merge na main continua dependendo da aprovação do grupo. Verificações pertinentes aos ajustes finais: 30 testes aprovados.
