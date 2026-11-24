# Build e instalação no Windows

O instalador oficial é gerado em um runner `windows-latest` pelo GitHub Actions. O jogo instalado é independente de Python e Pygame. O `.zip` portátil contém a pasta do PyInstaller e também não exige instalação de Python.

## Gerar localmente

Pré-requisitos: Windows, Python 3.12 ou superior de **64 bits** e Inno Setup 6 instalado. O script cria `.venv-build`, instala `requirements.txt` e `requirements-build.txt`, gera `dist/ScapeFromStoneDeCut` e compila o instalador.

```bat
installer\build_installer.bat
```

Para compilar outra versão sem alterar `VERSION`, passe-a como argumento:

```bat
installer\build_installer.bat 1.2.3
```

O resultado fica na raiz do projeto, ao lado de `main.py`, em `ScapeFromStoneDeCut-Setup-x.y.z.exe`. A pasta PyInstaller fica em `dist/ScapeFromStoneDeCut`. O Inno Setup pode ser baixado em [jrsoftware.org/isdl.php](https://jrsoftware.org/isdl.php); o script procura `ISCC.exe` no PATH e nos locais usuais.

## GitHub Actions e publicação

Em **Actions → Build Windows → Run workflow**, o build usa a versão do arquivo `VERSION`. Em tags, a versão vem do próprio nome: `v1.2.3` gera `1.2.3`. O workflow publica o instalador e o ZIP portátil como artefatos; em tags `v*`, anexa ambos a um GitHub Release.

Para publicar uma versão, atualize `VERSION` para `x.y.z`, envie a alteração ao repositório e crie/envie a tag correspondente `vX.Y.Z`. Por exemplo:

```bash
git tag v1.2.3
git push origin v1.2.3
```

O workflow não roda em pushes comuns para `main`. Cada arquivo anexado a Release precisa respeitar o limite de 2 GB do GitHub.

## Instalar, atualizar e desinstalar

O assistente instala por usuário, por padrão em `%LOCALAPPDATA%\Programs\ScapeFromStoneDeCut`, cria atalho no Menu Iniciar e oferece um atalho opcional na Área de Trabalho (desmarcado por padrão). A opção para executar o jogo ao terminar também fica desmarcada por padrão. Não é necessário administrador.

Saves e configurações ficam fora da pasta de instalação em `%LOCALAPPDATA%\ScapeFromStoneDeCut` (`saves` e `settings`). Instalar uma versão nova na mesma pasta atualiza os arquivos e preserva esses dados. O desinstalador remove o jogo, os atalhos e o registro do Windows. Ao final, pergunta se deseja apagar saves e configurações; a resposta padrão é **Não**.

## Problemas comuns

- **“O Windows protegeu o computador” (SmartScreen):** builds sem assinatura digital podem exibir esse aviso. Confira se baixou o instalador do Release esperado; se decidir executá-lo, clique em **Mais informações** e depois em **Executar assim mesmo**.
- **Aviso ou bloqueio do antivírus:** alguns antivírus podem sinalizar executáveis e instaladores sem assinatura digital. Confirme a origem do arquivo e siga a política de segurança da sua máquina; o projeto não fornece certificado nem promete assinatura digital.
- **ISCC.exe não encontrado no build local:** instale o Inno Setup 6 e execute novamente `installer\build_installer.bat`.
- **O instalador não fecha o jogo:** feche `ScapeFromStoneDeCut.exe` e tente novamente. O assistente usa a detecção de aplicativos do Inno Setup para solicitar o fechamento.

## Checklist de teste manual no Windows

- [ ] Instalar em uma máquina sem Python.
- [ ] Abrir o jogo pelo atalho do Menu Iniciar.
- [ ] Criar um save e jogar o tutorial.
- [ ] Abrir Mochila e Loja; confirmar que o áudio funciona.
- [ ] Fechar e reabrir o jogo; conferir que o save foi preservado.
- [ ] Instalar uma versão nova por cima e confirmar que o save continua disponível.
- [ ] Desinstalar e confirmar que os saves são preservados por padrão.
- [ ] Instalar novamente e iniciar o jogo.

## Limitações conhecidas

O repositório não contém um arquivo `.ico` nem `LICENSE`: por isso o instalador usa o ícone padrão do Inno Setup e não mostra página de licença. A pasta `assets/` ocupa aproximadamente 332 MiB; o tamanho final do pacote deve ser medido no runner Windows e precisa ficar abaixo de 2 GB para anexos ao Release.
