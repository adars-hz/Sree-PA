' SREE Desktop Application Launcher (100% Silent - Zero Console Windows)
' Automatically starts Ollama & SREE backend in background if needed, then opens the native App window.

Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

RootDir = FSO.GetParentFolderName(WScript.ScriptFullName)
Cmd = "pythonw.exe """ & RootDir & "\scripts\desktop_app.py"""

WshShell.CurrentDirectory = RootDir
WshShell.Run Cmd, 0, False

