#ifndef MyAppVersion
  #define MyAppVersion "0.1.1"
#endif

#define MyAppName "Scape From Stone de Cut"
#define MyAppPublisher "CyberGames"
#define MyAppExeName "ScapeFromStoneDeCut.exe"

[Setup]
AppId={{C92D740B-47E8-460D-B4E5-2CA152886C3A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\ScapeFromStoneDeCut
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..
OutputBaseFilename=ScapeFromStoneDeCut-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
CloseApplicationsFilter={#MyAppExeName}
RestartApplications=no
UninstallDisplayName={#MyAppName}
; Não há .ico no repositório. Quando houver um ícone aprovado, descomente:
; SetupIconFile=..\assets\icon.ico
; UninstallDisplayIcon={app}\ScapeFromStoneDeCut.exe

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar um atalho na Área de Trabalho"; GroupDescription: "Atalhos adicionais:"; Flags: unchecked

[Files]
Source: "..\dist\ScapeFromStoneDeCut\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; A pasta _internal contém os recursos/runtime da versão anterior do PyInstaller.
; Removê-la antes da cópia evita deixar arquivos antigos órfãos em atualizações.
[InstallDelete]
Type: filesandordirs; Name: "{app}\_internal"
Type: files; Name: "{app}\ScapeFromStoneDeCut.exe"

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Executar o jogo"; Flags: postinstall nowait skipifsilent unchecked

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataDirectory: String;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    if MsgBox('Deseja também apagar seus saves e configurações?',
      mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
    begin
      DataDirectory := ExpandConstant('{localappdata}\ScapeFromStoneDeCut');
      if DirExists(DataDirectory) then
        DelTree(DataDirectory, True, True, True);
    end;
  end;
end;
