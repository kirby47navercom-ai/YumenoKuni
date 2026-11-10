#requires -Version 7.0
$ErrorActionPreference='Stop'
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..')).TrimEnd('\')
$taskBin=[IO.Path]::GetFullPath((Get-Content -LiteralPath (Join-Path $taskRoot 'Game/build-result.json') -Raw -Encoding utf8 | ConvertFrom-Json).executable)
$taskCurrent=Split-Path -Parent $taskBin
$taskQuarantine=Join-Path $taskRoot '_삭제대기_2026-10-29_추가'
if(Test-Path -LiteralPath (Join-Path $taskQuarantine 'move-receipt.json')){throw 'Additional move already recorded; preserve its receipt and inventory rather than rerunning'}
$taskActive=@(Get-CimInstance Win32_Process -Filter "Name LIKE 'HBGame_%'" | ForEach-Object {$_.ExecutablePath} | Where-Object {$_})
$taskCandidates=@(Get-ChildItem -LiteralPath (Join-Path $taskRoot 'Game/Builds/windows-release') -Directory | Where-Object {$_.FullName -ne $taskCurrent})
foreach($taskRun in Get-ChildItem -LiteralPath (Join-Path $taskRoot 'Game/Saved') -Directory -Filter 'nonstop-*'){
    foreach($taskCache in @((Join-Path $taskRun.FullName 'LocalAppData'),(Join-Path $taskRun.FullName 'UserData/WebView2'))){
        if(Test-Path -LiteralPath $taskCache){$taskCandidates+=Get-Item -LiteralPath $taskCache}
    }
}
$taskRows=[Collections.Generic.List[object]]::new()
$taskUnits=[Collections.Generic.List[object]]::new()
foreach($taskCandidate in $taskCandidates){
    $taskSource=[IO.Path]::GetFullPath($taskCandidate.FullName).TrimEnd('\')
    if(-not $taskSource.StartsWith($taskRoot+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Source escaped workspace'}
    if($taskCurrent.Equals($taskSource,[StringComparison]::OrdinalIgnoreCase) -or $taskCurrent.StartsWith($taskSource+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Latest build protected'}
    if($taskActive | Where-Object {$_.StartsWith($taskSource+'\',[StringComparison]::OrdinalIgnoreCase)}){continue}
    $taskRelative=[IO.Path]::GetRelativePath($taskRoot,$taskSource)
    $taskDestination=[IO.Path]::GetFullPath((Join-Path $taskQuarantine $taskRelative))
    if(-not $taskDestination.StartsWith($taskQuarantine+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Destination escaped quarantine'}
    if(Test-Path -LiteralPath $taskDestination){throw 'Destination collision; no overwrite'}
    $taskFiles=@(Get-ChildItem -LiteralPath $taskSource -File -Recurse -Force)
    foreach($taskFile in $taskFiles){
        $taskRows.Add([pscustomobject]@{original_path=[IO.Path]::GetRelativePath($taskRoot,$taskFile.FullName);current_path=[IO.Path]::GetRelativePath($taskRoot,(Join-Path $taskDestination ([IO.Path]::GetRelativePath($taskSource,$taskFile.FullName))));bytes=$taskFile.Length;deleted=$false})
    }
    New-Item -ItemType Directory -Path (Split-Path -Parent $taskDestination) -Force | Out-Null
    Move-Item -LiteralPath $taskSource -Destination $taskDestination
    if(Test-Path -LiteralPath $taskSource){throw 'Source remains after move'}
    $taskUnits.Add([pscustomobject]@{source=$taskRelative;destination=[IO.Path]::GetRelativePath($taskRoot,$taskDestination);status='moved'})
}
foreach($taskRow in $taskRows){
    $taskMoved=Get-Item -LiteralPath (Join-Path $taskRoot $taskRow.current_path)
    if($taskMoved.Length -ne $taskRow.bytes){throw 'Moved size differs'}
}
if(-not (Test-Path -LiteralPath $taskBin)){throw 'Latest executable missing'}
$taskReceipt=[ordered]@{scope='Additional obsolete own-game builds and closed nonstop-test browser caches only; reversible move; no deletion';quarantine=[IO.Path]::GetRelativePath($taskRoot,$taskQuarantine);current_build_preserved=$taskCurrent;moved_files=$taskRows.Count;moved_bytes=($taskRows | Measure-Object -Property bytes -Sum).Sum;deleted_bytes=0;disk_bytes_freed=0;units=@($taskUnits);rows=@($taskRows)}
$taskList=Join-Path $taskRoot 'docs/analysis/storage_cleanup_2026-10-29'
New-Item -ItemType Directory -Path $taskList -Force | Out-Null
$taskReceipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $taskList 'additional_files.json') -Encoding utf8
$taskRows | Export-Csv -LiteralPath (Join-Path $taskList 'additional_files.csv') -NoTypeInformation -Encoding utf8
$taskReceipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $taskQuarantine 'move-receipt.json') -Encoding utf8
Write-Output (@{moved_files=$taskRows.Count;moved_bytes=$taskReceipt.moved_bytes;units=$taskUnits.Count;deleted_bytes=0;latest_build_present=$true} | ConvertTo-Json)
