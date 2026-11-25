# Build Android (APK)

O projeto usa Pygame/SDL2. Os APKs são compilados com Buildozer e
python-for-android dentro de Linux; no Windows, use WSL 2 com Ubuntu 24.04.

## Preparar o WSL

No PowerShell como administrador, instale o WSL 2 e a distro Ubuntu 24.04 se
necessário:

```powershell
wsl --install -d Ubuntu-24.04
```

Abra o Ubuntu uma vez para concluir a criação do usuário e, no terminal dele,
instale as ferramentas nativas:

```bash
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip python3-venv \
  autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev \
  libtinfo6 cmake libffi-dev libssl-dev automake autopoint gettext rsync
```

## Gerar o APK localmente

No terminal Ubuntu/WSL, execute o script do checkout. O script prepara um
ambiente virtual do Buildozer, compila numa cópia dentro do filesystem Linux
(mais rápido e confiável que `/mnt/c`) e copia o resultado de volta ao projeto:

```bash
cd "/mnt/c/caminho/para/Scape-from-stone-de-cut"
bash android/build_apk.sh
```

A primeira compilação baixa o SDK/NDK e pode levar bastante tempo. Por padrão,
o APK de depuração fica em `android/output/ScapeFromStoneDeCut-{versão}-debug.apk`.
A versão vem de `VERSION`; a configuração mantém a tela em paisagem e grava
saves e preferências no armazenamento privado do app, em `ScapeFromStoneDeCut/`.

## APK de release assinado

Para gerar um APK instalável de release, use uma chave de assinatura permanente
e execute `bash android/build_apk.sh release`. Configure no ambiente WSL as
variáveis `P4A_RELEASE_KEYSTORE`, `P4A_RELEASE_KEYSTORE_PASSWD`,
`P4A_RELEASE_KEYALIAS` e `P4A_RELEASE_KEYALIAS_PASSWD`. O script valida todas
antes de começar e grava `android/output/ScapeFromStoneDeCut-{versão}-release.apk`.

Guarde a keystore e suas senhas em local seguro, fora do repositório, e faça
backup. Todas as futuras atualizações instaláveis precisam usar a mesma chave;
perdê-la impede atualizar a instalação existente. Nunca envie a keystore ao Git
ou como artefato público. Uma keystore de upload é criada com `keytool -genkeypair`
incluído no JDK. O APK de debug tem outra assinatura e não atualiza a instalação
de release.

A validação final de toque, áudio, instalação/atualização e persistência deve ser
feita em aparelho Android físico. A interface foi desenhada para 16:9 e pode
mostrar áreas de letterbox em telas com outra proporção.
