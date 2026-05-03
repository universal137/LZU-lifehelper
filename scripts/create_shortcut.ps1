$root = Split-Path -Parent $PSScriptRoot
$shortcutName = ([string][char]0x5170) + [char]0x5927 + [char]0x751F + [char]0x6D3B + [char]0x52A9 + [char]0x624B + ".lnk"
$shortcutPath = Join-Path $root $shortcutName
$targetPath = Join-Path $root "run_desktop.bat"

$wshShell = New-Object -ComObject WScript.Shell
$shortcut = $wshShell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $targetPath
$shortcut.WorkingDirectory = $root
$shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,220"
$shortcut.Save()

Write-Output "快捷方式已创建: $shortcutPath"
