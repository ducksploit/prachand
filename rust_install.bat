@echo off

REM Set the URL for the Rustup installation script
set rustup_url=https://win.rustup.rs/x86_64

REM Set the path where the script will be downloaded
set rustup_path=%temp%\rustup-init.exe

REM Download the Rustup installation script using Bitsadmin
Bitsadmin /transfer rustup /download /priority normal %rustup_url% %rustup_path%

REM Run the installation script with default options
%rustup_path% -y

REM Add the Rustup binary directory to your PATH
set PATH=%PATH%;%USERPROFILE%\.cargo\bin

REM Remove the installation script
del %rustup_path%
