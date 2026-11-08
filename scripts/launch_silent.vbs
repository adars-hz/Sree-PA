' SREE Silent Windows Background Launcher
' Starts the background speech listener with zero visible command prompt windows.

Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

ScriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)
RootDir = FSO.GetParentFolderName(ScriptDir)
PsScript = ScriptDir & "\background_listener.ps1"

Cmd = "powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & PsScript & """"
WshShell.Run Cmd, 0, False

