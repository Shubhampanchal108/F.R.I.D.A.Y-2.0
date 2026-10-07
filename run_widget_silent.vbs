Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.Run """.\.venv\Scripts\pythonw.exe"" friday_widget.py", 0, False
Set WshShell = Nothing
