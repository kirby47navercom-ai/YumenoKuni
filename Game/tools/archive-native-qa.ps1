param([switch]$DryRun,[string[]]$RunName)
$ErrorActionPreference='Stop'
$taskGame=(Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
$taskRepo=Split-Path -Parent $taskGame
$taskSaved=(Resolve-Path -LiteralPath (Join-Path $taskGame 'Saved')).Path
$taskArchive=[IO.Path]::GetFullPath((Join-Path $taskRepo '삭제 대기'))
if([IO.Path]::GetDirectoryName($taskArchive) -ne $taskRepo){throw 'Unsafe quarantine root'}
if((Test-Path -LiteralPath $taskArchive) -and ((Get-Item -LiteralPath $taskArchive).Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Quarantine is a reparse point'}
$taskBatch=Join-Path $taskArchive ('native-qa-'+(Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
$taskProcesses=@(Get-CimInstance Win32_Process -Filter "Name = 'node.exe' OR Name LIKE 'HBGame%' OR Name LIKE 'HBScript%'")
$taskRows=@()
$taskRuns=@(Get-ChildItem -LiteralPath $taskSaved -Directory|Where-Object{$_.Name -match '^native-(startup|continue|mode-matrix|world-save|legacy-save|scroll-live|migration-live|outdoor|all-tasks|all-choices|performance|ending-replay|widget-snapshot|widget-paint|canvas-input|canvas-aim|gpu-trial|gpu-panic|gpu-anagram|gpu-showdown|hud-palette|trial-cost)-\d+$'})
foreach($taskPacket in Get-ChildItem -LiteralPath $taskSaved -Directory|Where-Object{$_.Name -match '^native-packet-exit-\d+$'}){$taskRuns+=@(Get-ChildItem -LiteralPath $taskPacket.FullName -Directory|Where-Object{$_.Name -in @('shipping-baseline','owned-failure-fix','shipping-fixed')})}
foreach($taskFps in Get-ChildItem -LiteralPath $taskSaved -Directory|Where-Object{$_.Name -match '^native-fps-settings-\d+$'}){$taskRuns+=@(Get-ChildItem -LiteralPath $taskFps.FullName -Directory|Where-Object{$_.Name -in @('first','restart')})}
foreach($taskDisplay in Get-ChildItem -LiteralPath $taskSaved -Directory|Where-Object{$_.Name -match '^native-display-\d+$'}){$taskRuns+=@(Get-ChildItem -LiteralPath $taskDisplay.FullName -Directory|Where-Object{$_.Name -in @('first','second')})}
foreach($taskArt in Get-ChildItem -LiteralPath $taskSaved -Directory|Where-Object{$_.Name -match '^native-backgrounds-\d+$'}){$taskRuns+=@(Get-ChildItem -LiteralPath $taskArt.FullName -Directory|Where-Object{$_.Name -in @('title','roof_garden_day','parade_float_day')})}
if($RunName){$taskRuns=@($taskRuns|Where-Object{$_.Name -in $RunName})}
foreach($taskRun in $taskRuns){
 $taskPackage=Join-Path $taskRun.FullName 'package'
 $taskReceipt=Join-Path $taskRun.FullName 'owned-package.json'
 if(-not (Test-Path -LiteralPath $taskPackage -PathType Container) -or -not (Test-Path -LiteralPath $taskReceipt -PathType Leaf)){continue}
 $taskFull=(Resolve-Path -LiteralPath $taskPackage).Path

 if($taskFull -eq [IO.Path]::GetFullPath((Join-Path $taskSaved 'native-performance-1793612689148\package'))){continue}
 $taskRelative=$taskFull.Substring($taskSaved.Length+1)
 if(-not $taskFull.StartsWith($taskSaved+'\',[StringComparison]::OrdinalIgnoreCase) -or $taskRelative -notmatch '^(?:native-(?:startup|continue|mode-matrix|world-save|legacy-save|scroll-live|migration-live|outdoor|all-tasks|all-choices|performance|ending-replay|widget-snapshot|widget-paint|canvas-input|canvas-aim|gpu-trial|gpu-panic|gpu-anagram|gpu-showdown|hud-palette|trial-cost)-\d+\\package|native-fps-settings-\d+\\(?:first|restart)\\package|native-display-\d+\\(?:first|second)\\package|native-backgrounds-\d+\\(?:title|roof_garden_day|parade_float_day)\\package|native-packet-exit-\d+\\(?:shipping-baseline|owned-failure-fix|shipping-fixed)\\package)$'){throw 'Unsafe owned QA package path'}
 $taskProof=Get-Content -LiteralPath $taskReceipt -Raw -Encoding utf8|ConvertFrom-Json
 if([IO.Path]::GetFullPath($taskProof.output) -ne $taskFull -or $taskProof.sourcePackageOrEngineModified -ne $false){throw 'Missing immutable QA ownership proof'}
 $taskLive=@($taskProcesses|Where-Object{($_.ExecutablePath -and $_.ExecutablePath.StartsWith($taskFull+'\',[StringComparison]::OrdinalIgnoreCase)) -or ($_.CommandLine -and $_.CommandLine.IndexOf($taskFull,[StringComparison]::OrdinalIgnoreCase) -ge 0)})
 if($taskLive.Count){continue}
 $taskAncestor=$taskFull
 while($taskAncestor -ne $taskRepo){if((Get-Item -LiteralPath $taskAncestor).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Reparse ancestor'};$taskAncestor=Split-Path -Parent $taskAncestor}
 if(@(Get-ChildItem -LiteralPath $taskFull -Recurse -Force -Attributes ReparsePoint).Count){throw 'Reparse descendant'}
 $taskManifest=Get-Content -LiteralPath (Join-Path $taskFull 'game.hbpack.json') -Raw -Encoding utf8|ConvertFrom-Json
 if($taskManifest.id -ne '004a6371-3a84-4fc3-8b54-31a5001740dd' -or $taskManifest.windowsRuntime -ne 'native'){throw 'Wrong QA package identity'}
 $taskDestination=[IO.Path]::GetFullPath((Join-Path $taskBatch $taskRelative))
 if(-not $taskDestination.StartsWith($taskBatch+'\',[StringComparison]::OrdinalIgnoreCase) -or (Test-Path -LiteralPath $taskDestination)){throw 'Unsafe quarantine destination'}
 $taskBefore=Get-ChildItem -LiteralPath $taskFull -File -Recurse -Force|Measure-Object Length -Sum
 if(-not $DryRun){
  # Retain the complete hash inventory beside the reports after the disposable
  # package moves, so acceptance tools can still verify exact runtime owners.
  Copy-Item -LiteralPath (Join-Path $taskFull 'game.hbpack.json') -Destination (Join-Path $taskRun.FullName 'package-manifest.json') -Force
  # Verify exact resolved source again immediately before the move.
  if((Resolve-Path -LiteralPath $taskFull).Path -ne $taskFull -or -not $taskFull.StartsWith($taskSaved+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Final source mismatch'}
  New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($taskDestination)) -Force|Out-Null
  Move-Item -LiteralPath $taskFull -Destination $taskDestination
  $taskAfter=Get-ChildItem -LiteralPath $taskDestination -File -Recurse -Force|Measure-Object Length -Sum
  if((Test-Path -LiteralPath $taskFull) -or $taskBefore.Count -ne $taskAfter.Count -or $taskBefore.Sum -ne $taskAfter.Sum){throw 'Move inventory mismatch'}
 }
 $taskRows+=@{source=$taskFull;destination=$taskDestination;files=$taskBefore.Count;logicalBytes=$taskBefore.Sum;moved=(-not $DryRun)}
}
$taskResult=@{dryRun=[bool]$DryRun;deleted=0;physicalBytesReclaimed=0;policy='Move only closed owned QA packages. Preserve all reports, captures, State/Saves, source, current/previous builds. Shared hardlink bytes are logical, not disk reclaimed.';records=$taskRows}
$taskOut=Join-Path $taskSaved ('native-qa-retention-'+(Get-Date -Format 'yyyyMMdd-HHmmss-fff')+'.json')
$taskResult|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $taskOut -Encoding utf8
if(-not $DryRun -and $taskRows.Count){$taskResult|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $taskBatch '이동내역.json') -Encoding utf8}
@{receipt=$taskOut;moved=@($taskRows|Where-Object moved).Count;planned=$taskRows.Count;deleted=0;physicalBytesReclaimed=0}|ConvertTo-Json -Compress
