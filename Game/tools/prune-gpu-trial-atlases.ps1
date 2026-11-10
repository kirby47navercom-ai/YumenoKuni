param([switch]$DryRun)
$ErrorActionPreference='Stop'
$taskGame=(Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
$taskRepo=Split-Path -Parent $taskGame
$taskRoot=(Resolve-Path -LiteralPath (Join-Path $taskGame 'Assets/Art/ui/gpu_trial')).Path
$taskLayout=Get-Content -LiteralPath (Join-Path $taskGame 'Assets/Data/gpu_trial_layout.json') -Raw -Encoding utf8|ConvertFrom-Json
$taskWanted=@{}
foreach($taskBatch in (@($taskLayout.batches)+@($taskLayout.pages))){
 $taskSprite=[IO.Path]::GetFileName($taskBatch.sprite)
 if($taskSprite -notmatch '^g_[0-9a-f]{8}_(atlas|line)\.hbsprite\.json$'){throw 'Unexpected owned font atlas'}
 $taskWanted[$taskSprite]=$true
 $taskSpritePath=Join-Path $taskRoot $taskSprite
 $taskTexture=(Get-Content -LiteralPath $taskSpritePath -Raw -Encoding utf8|ConvertFrom-Json).texture
 $taskWanted[[IO.Path]::GetFileName($taskTexture)]=$true
}
$taskArchive=[IO.Path]::GetFullPath((Join-Path $taskRepo '삭제 대기'))
if([IO.Path]::GetDirectoryName($taskArchive) -ne $taskRepo){throw 'Unsafe quarantine root'}
if((Test-Path -LiteralPath $taskArchive) -and ((Get-Item -LiteralPath $taskArchive).Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Quarantine is a reparse point'}
$taskDestination=Join-Path $taskArchive ('gpu-atlases-'+(Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
$taskRows=@()
foreach($taskFile in Get-ChildItem -LiteralPath $taskRoot -File){
 if($taskFile.Name -notmatch '^g_[0-9a-f]{8}_atlas\.(png|hbsprite\.json)$' -or $taskWanted.ContainsKey($taskFile.Name)){continue}
 $taskSource=(Resolve-Path -LiteralPath $taskFile.FullName).Path
 $taskTarget=[IO.Path]::GetFullPath((Join-Path $taskDestination $taskFile.Name))
 if(-not $taskSource.StartsWith($taskRoot+'\',[StringComparison]::OrdinalIgnoreCase) -or [IO.Path]::GetDirectoryName($taskTarget) -ne $taskDestination){throw 'Unsafe generated atlas move'}
 if($taskFile.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Generated atlas is a reparse point'}
 $taskHash=(Get-FileHash -LiteralPath $taskSource -Algorithm SHA256).Hash
 if(-not $DryRun){
  New-Item -ItemType Directory -Path $taskDestination -Force|Out-Null
  Move-Item -LiteralPath $taskSource -Destination $taskTarget
  if((Get-FileHash -LiteralPath $taskTarget -Algorithm SHA256).Hash -ne $taskHash){throw 'Moved atlas hash mismatch'}
 }
 $taskRows+=@{source=$taskSource;target=$taskTarget;sha256=$taskHash;bytes=$taskFile.Length}
}
$taskReceipt=Join-Path $taskGame ('Saved/gpu-atlas-retention-'+(Get-Date -Format 'yyyyMMdd-HHmmss-fff')+'.json')
@{dryRun=[bool]$DryRun;deleted=0;physicalBytesReclaimed=0;records=$taskRows}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $taskReceipt -Encoding utf8
@{receipt=$taskReceipt;unreferenced=$taskRows.Count;moved=$(if($DryRun){0}else{$taskRows.Count});deleted=0}|ConvertTo-Json -Compress
