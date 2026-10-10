' =============================================================================
' F.R.I.D.A.Y 2.0 // SILENT AUTO-START BOOTSTRAPPER
' =============================================================================
' Launches friday_autostart.py completely invisibly in the background on startup.
' =============================================================================

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Target Friday Directory
FridayDir = "c:\Users\j\OneDrive\Desktop\shubham studio\F.R.I.D.A.Y"
If Not fso.FolderExists(FridayDir) Then
    ' Fallback to script's own parent folder if project directory moved
    FridayDir = fso.GetParentFolderName(WScript.ScriptFullName)
End If

WshShell.CurrentDirectory = FridayDir

PythonwExe = FridayDir & "\.venv\Scripts\pythonw.exe"
If Not fso.FileExists(PythonwExe) Then
    PythonwExe = "pythonw.exe"
End If

AutoStartScript = FridayDir & "\friday_autostart.py"

' Run with window style 0 (completely hidden) and do not wait
WshShell.Run """" & PythonwExe & """ """ & AutoStartScript & """", 0, False

Set WshShell = Nothing
Set fso = Nothing
