[Setup]
AppName=SAR - Sistema de Automacao de Recolocacao
AppVersion=1.0
AppPublisher=Ricardo Alisson Dantas Macedo
DefaultDirName={userappdata}\SAR
DefaultGroupName=SAR
DisableProgramGroupPage=yes
OutputDir=.
OutputBaseFilename=SAR_Setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest
WizardStyle=modern
SetupIconFile=
UninstallDisplayName=SAR - Sistema de Automacao de Recolocacao

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Files]
Source: "SAR.exe"; DestDir: "{userappdata}\SAR"; Flags: ignoreversion
Source: "instalacao.dat"; DestDir: "{userappdata}\SAR"; Flags: ignoreversion

[Icons]
Name: "{userdesktop}\SAR"; Filename: "{userappdata}\SAR\SAR.exe"; Comment: "Sistema de Automacao de Recolocacao"

[Run]
Filename: "{userappdata}\SAR\SAR.exe"; Description: "Iniciar o SAR agora"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\SAR"
