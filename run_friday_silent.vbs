' =============================================================================
' F.R.I.D.A.Y 2.0 // UNIVERSAL SILENT LAUNCHER
' =============================================================================
' Double-click from ANYWHERE on Windows to launch Friday Widget silently!
' =============================================================================

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

FridayDir = "c:\Users\j\OneDrive\Desktop\shubham studio\F.R.I.D.A.Y"
If Not fso.FolderExists(FridayDir) Then
    FridayDir = fso.GetParentFolderName(WScript.ScriptFullName)
End If

WshShell.CurrentDirectory = FridayDir

PythonwExe = FridayDir & "\.venv\Scripts\pythonw.exe"
If Not fso.FileExists(PythonwExe) Then
    PythonwExe = "pythonw.exe"
End If

WidgetScript = FridayDir & "\friday_widget.py"

' Run with window style 0 (hidden)
WshShell.Run """" & PythonwExe & """ """ & WidgetScript & """", 0, False

Set WshShell = Nothing
Set fso = Nothing
