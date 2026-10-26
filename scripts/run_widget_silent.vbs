Set fso = CreateObject("Scripting.FileSystemObject")
Set WshShell = CreateObject("WScript.Shell")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
rootDir = fso.GetParentFolderName(scriptDir)
WshShell.CurrentDirectory = rootDir
WshShell.Run """.\.venv\Scripts\pythonw.exe"" friday_widget.py", 0, False
Set WshShell = Nothing
Set fso = Nothing
