# 바탕화면에 "대사 번역기" 바로가기를 아이콘과 함께 만든다.
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$desktop = [Environment]::GetFolderPath('Desktop')
$lnkPath = Join-Path $desktop '대사 번역기.lnk'

$shell = New-Object -ComObject WScript.Shell
$lnk = $shell.CreateShortcut($lnkPath)
$lnk.TargetPath = Join-Path $dir 'start.bat'
$lnk.WorkingDirectory = $dir
$lnk.IconLocation = (Join-Path $dir 'icon.ico') + ',0'
$lnk.Description = '동영상 대사를 한국어로 번역'
$lnk.Save()

Write-Host "바로가기를 만들었습니다: $lnkPath"
