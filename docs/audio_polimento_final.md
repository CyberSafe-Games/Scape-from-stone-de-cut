# Polimento antes da PR final — 11/11/2026

## Main remota

Conferida por `git ls-remote` e `git fetch origin`: `87456fdd16d3a663b78791b9096df586a2c8f04b`.
O único commit da main além da HEAD local é o merge da PR #13 de áudio.
`git diff HEAD origin/main --name-only` está vazio: as árvores commitadas são
iguais. Nenhuma nova ação sem som foi identificada nessa atualização.
Não foi feito merge, commit, push nem publicação de PR nesta revisão.

## Soco

O arquivo anterior `dragon-studio-hard-punch-sfx-515251_sync.ogg` apresenta
2.474 amostras no limite de 16 bits, pico próximo de 0 dBFS e RMS ativo
de -5,385 dBFS. O ganho 0,14 atenuava a reprodução, mas não eliminava a
distorção já presente na gravação.

Novo derivado: `soco_impacto_suave_v2.ogg`, sem sobrescrever o anterior.
Preparação reproduzível em `devtools/polish_punch_audio.py`; receita e hashes em
`docs/soco_polimento_v2.json`. Usa estimativa de declipping, redução de graves
subsônicos/agudos ásperos e fades curtos. Declipping não recupera informação
perdida; a qualidade perceptiva continua dependendo da escuta do usuário.

Após codificação e decodificação no Pygame: pico -16,233 dBFS, RMS ativo
-32,007 dBFS e zero amostras no limite. O ganho fica incorporado no recurso;
`SOUND_VOLUMES` usa 1,0 para não aplicar novamente a atenuação antiga.
O contato continua presente nos primeiros 160 ms e a duração é preservada
dentro de 25 ms. Gatilhos, janelas e volumes de chamada não foram alterados.
Todos os usuários do identificador de soco, inclusive inimigos, recebem o ajuste.

## Revisão dos demais sons

Auditoria dos 80 efeitos registrados: arquivos carregáveis, todos com ganho
explícito, nenhum excedendo pico -9 dBFS ou RMS ativo -22 dBFS em reprodução
individual com controles em 100%. Relatório: `docs/audio_mix_audit.json`.
Os demais efeitos e as quatro músicas aprovadas foram preservados.

Essas referências não são medição de LUFS ou true peak, nem garantem ausência
de saturação na soma de múltiplos canais. Não houve escuta crítica pelo agente.
Arquivos antigos com saturação e efeitos percebidos como ásperos precisam de
conferência no jogo antes de qualquer troca adicional de timbre.

## Validação perceptiva pendente

No jogo completo, comparar Soco Simples e golpes físicos dos inimigos, depois
investida/machados, projéteis, poções/escudos, chefes e transições musicais.
Usar o mesmo volume do sistema e as mesmas preferências na comparação.
Testes automatizados não equivalem à aprovação dessa escuta.

As cartas geradas são apenas material para o grupo e não foram integradas.
Novas cartas, regras, sprites e saves estão fora deste ajuste.
