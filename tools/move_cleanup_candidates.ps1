$ErrorActionPreference='Stop'
$moveRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..')).TrimEnd('\')
$moveFolder=Join-Path $moveRoot '_삭제대기_2026-10-29'
$movePlan=Get-Content -LiteralPath (Join-Path $moveFolder 'move-plan.json') -Raw -Encoding utf8 | ConvertFrom-Json
$currentBuild=[IO.Path]::GetFullPath((Join-Path $moveRoot $movePlan.current_build_preserved)).TrimEnd('\')
$activeExecutables=@(Get-CimInstance Win32_Process -Filter "Name LIKE 'HBGame_%'" | ForEach-Object {$_.ExecutablePath} | Where-Object {$_})
$receipt=[Collections.Generic.List[object]]::new()
$moveBytes=[long]0
foreach($unit in $movePlan.units){
    $source=[IO.Path]::GetFullPath((Join-Path $moveRoot $unit.source))
    $destination=[IO.Path]::GetFullPath((Join-Path $moveRoot $unit.destination))
    if(-not $source.StartsWith($moveRoot+'\',[StringComparison]::OrdinalIgnoreCase) -or -not $destination.StartsWith($moveFolder+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Move path escaped intended workspace/quarantine'}
    if($currentBuild.Equals($source,[StringComparison]::OrdinalIgnoreCase) -or $currentBuild.StartsWith($source+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Current build cannot be moved'}
    if($activeExecutables | Where-Object {$_.StartsWith($source+'\',[StringComparison]::OrdinalIgnoreCase)}){
        $receipt.Add(@{source=$unit.source;destination=$unit.destination;status='active_build_preserved';bytes=0});continue
    }
    if($source.StartsWith((Join-Path $moveRoot '.git')+'\',[StringComparison]::OrdinalIgnoreCase) -and -not ([IO.Path]::GetFileName($source).StartsWith('tmp_obj_'))){throw 'Regular Git object/ref cannot be moved'}
    try{
        if(-not (Test-Path -LiteralPath $source)){
            if(Test-Path -LiteralPath $destination){$receipt.Add(@{source=$unit.source;destination=$unit.destination;status='already_moved';bytes=$unit.bytes});$moveBytes+=$unit.bytes;continue}
            throw 'Source and destination both missing'
        }
        if(Test-Path -LiteralPath $destination){throw 'Destination collision; no overwrite'}
        New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($destination)) -Force | Out-Null
        Move-Item -LiteralPath $source -Destination $destination
        $receipt.Add(@{source=$unit.source;destination=$unit.destination;status='moved';bytes=$unit.bytes})
        $moveBytes+=$unit.bytes
    }catch{$receipt.Add(@{source=$unit.source;destination=$unit.destination;status='failed';error=$_.Exception.Message;bytes=0})}
    if($receipt.Count%250 -eq 0){Write-Output ("Processed {0}/{1}, moved {2:N2} GiB" -f $receipt.Count,$movePlan.units.Count,($moveBytes/1GB))}
}
$summary=@{operation='User-requested reversible move; no deletion';movedBytes=$moveBytes;units=$receipt;deletedBytes=0;currentBuildPreserved=(Test-Path -LiteralPath $currentBuild)}
$summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $moveFolder 'move-receipt.json') -Encoding utf8
Write-Output (@{movedBytes=$moveBytes;movedGiB=$moveBytes/1GB;failed=@($receipt | Where-Object {$_.status -eq 'failed'}).Count;units=$receipt.Count;receipt=(Join-Path $moveFolder 'move-receipt.json')} | ConvertTo-Json)
