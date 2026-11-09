param(
 [Parameter(Mandatory=$true)][string]$CurrentExecutable,
 [string]$PreviousExecutable = '',
 [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
$taskGameRoot = (Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
$taskProjectRoot = Split-Path -Parent $taskGameRoot
$taskArchiveRoot = [IO.Path]::GetFullPath((Join-Path $taskProjectRoot '삭제 대기'))
if ([IO.Path]::GetDirectoryName($taskArchiveRoot) -ne $taskProjectRoot) { throw 'Unsafe named quarantine root' }
if ((Test-Path -LiteralPath $taskArchiveRoot) -and ((Get-Item -LiteralPath $taskArchiveRoot).Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Quarantine root is a reparse point' }
$taskBuildRoot = (Resolve-Path -LiteralPath (Join-Path $taskGameRoot 'Builds')).Path
$taskSaved = (Resolve-Path -LiteralPath (Join-Path $taskGameRoot 'Saved')).Path
$taskBatch = Join-Path $taskArchiveRoot ('generated-'+(Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
$taskPlatforms = @('windows','windows-release')
function Test-BuildFolder([string]$taskFolder) {
 $taskPlatform = [IO.Path]::GetDirectoryName($taskFolder)
 return [IO.Path]::GetDirectoryName($taskPlatform) -eq $taskBuildRoot -and [IO.Path]::GetFileName($taskPlatform) -in $taskPlatforms
}
$taskKeep = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($taskExecutable in @($CurrentExecutable,$PreviousExecutable)) {
 if (-not $taskExecutable) { continue }
 $taskFull = [IO.Path]::GetFullPath($taskExecutable)
 $taskFolder = [IO.Path]::GetDirectoryName($taskFull)
 if (-not (Test-BuildFolder $taskFolder)) { throw 'Protected executable is not in an owned platform build folder' }
 if ($taskExecutable -eq $CurrentExecutable -and -not (Test-Path -LiteralPath $taskFull -PathType Leaf)) { throw 'Current executable is missing' }
 if (Test-Path -LiteralPath $taskFolder -PathType Container) { [void]$taskKeep.Add($taskFolder) }
}
# A concurrent art task has one explicit current artifact outside the global
# story build pointer. Protect only that validated current build, not history.
$taskArtPointer=Join-Path $taskSaved 'sculpted-environment-20261103/build-result.json'
if (Test-Path -LiteralPath $taskArtPointer -PathType Leaf) {
 $taskArt=Get-Content -LiteralPath $taskArtPointer -Raw -Encoding UTF8|ConvertFrom-Json
 if ($taskArt.environmentOnly -and $taskArt.executable) {
  $taskArtFull=[IO.Path]::GetFullPath([string]$taskArt.executable)
  $taskArtFolder=[IO.Path]::GetDirectoryName($taskArtFull)
  if ((Test-BuildFolder $taskArtFolder) -and (Test-Path -LiteralPath $taskArtFull -PathType Leaf)) { [void]$taskKeep.Add($taskArtFolder) }
 }
}
# Preserve both running packaged players and their isolated WebView profiles.
$taskProcesses = @(Get-CimInstance Win32_Process -Filter "Name = 'msedgewebview2.exe' OR Name = 'node.exe' OR Name LIKE 'HBGame%' OR Name LIKE 'HBEngine%'")
foreach ($taskProcess in $taskProcesses) {
 if ($taskProcess.ExecutablePath -and $taskProcess.ExecutablePath.StartsWith($taskBuildRoot + '\',[StringComparison]::OrdinalIgnoreCase)) {
  $taskRelative = $taskProcess.ExecutablePath.Substring($taskBuildRoot.Length+1)
  $taskParts = $taskRelative.Split([IO.Path]::DirectorySeparatorChar)
  if ($taskParts.Length -ge 3 -and $taskParts[0] -in $taskPlatforms) { [void]$taskKeep.Add((Join-Path (Join-Path $taskBuildRoot $taskParts[0]) $taskParts[1])) }
 }
}
$taskPlan = [Collections.Generic.List[object]]::new()
function Add-Candidate([string]$taskSource,[string]$taskReason) {
 $taskPath=(Resolve-Path -LiteralPath $taskSource).Path
 if (-not $taskPath.StartsWith($taskGameRoot+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Candidate outside Game' }
 $taskAncestor=$taskPath
 while ($taskAncestor -ne $taskProjectRoot) { if ((Get-Item -LiteralPath $taskAncestor).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Candidate has reparse ancestor' };$taskAncestor=Split-Path -Parent $taskAncestor }
 if (@(Get-ChildItem -LiteralPath $taskPath -Recurse -Force -Attributes ReparsePoint).Count) { throw 'Candidate contains reparse point' }
 $taskMeasure=Get-ChildItem -LiteralPath $taskPath -File -Recurse -Force|Measure-Object Length -Sum
 $taskRelative=$taskPath.Substring($taskProjectRoot.Length+1)
 $taskDestination=[IO.Path]::GetFullPath((Join-Path $taskBatch $taskRelative))
 if (-not $taskDestination.StartsWith($taskBatch+'\',[StringComparison]::OrdinalIgnoreCase) -or (Test-Path -LiteralPath $taskDestination)) { throw 'Unsafe quarantine destination' }
 $taskPlan.Add([pscustomobject]@{path=$taskPath;destination=$taskDestination;reason=$taskReason;bytes=[long]$taskMeasure.Sum;files=$taskMeasure.Count;moved=$false})
}
$taskBuildFolders=@(foreach($taskPlatform in $taskPlatforms){$taskPlatformPath=Join-Path $taskBuildRoot $taskPlatform;if(Test-Path -LiteralPath $taskPlatformPath){Get-ChildItem -LiteralPath $taskPlatformPath -Directory}})
foreach ($taskDirectory in $taskBuildFolders) {
 $taskPath = (Resolve-Path -LiteralPath $taskDirectory.FullName).Path
 if (-not (Test-BuildFolder $taskPath)) { throw 'Unsafe resolved build path' }
 if ($taskKeep.Contains($taskPath)) { continue }
 if ($taskDirectory.Name -notmatch '^\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}-\d{3}Z-[0-9a-f]{8}$') { continue }
 # Other editor/build jobs can create a folder before a player process exists.
 # Never move incomplete or recently written outputs while their writer runs.
 if (-not (Test-Path -LiteralPath (Join-Path $taskPath 'game.hbpack.json') -PathType Leaf) -or $taskDirectory.LastWriteTimeUtc -gt [DateTime]::UtcNow.AddMinutes(-10)) { [void]$taskKeep.Add($taskPath);continue }
 Add-Candidate $taskPath 'superseded-generated-build'
}
# Some older multi-case checks nest their isolated player beneath the run.
# Only UserData/WebView2 is disposable; neighboring saves, Sessions and proof stay.
foreach ($taskCache in Get-ChildItem -LiteralPath $taskSaved -Directory -Recurse -Filter 'WebView2') {
 if ($taskCache.Parent.Name -ne 'UserData') { continue }
 $taskProfile=(Resolve-Path -LiteralPath $taskCache.FullName).Path
 $taskLive=@($taskProcesses|Where-Object{$_.CommandLine -and $_.CommandLine.IndexOf($taskProfile,[StringComparison]::OrdinalIgnoreCase) -ge 0})
 if (-not $taskLive.Count) { Add-Candidate $taskProfile 'closed-isolated-WebView-cache; savegames/reports/sessions preserved' }
}
$taskReceipt = [ordered]@{policy='move-only; current + previous + active player builds; closed isolated WebView caches; preserve all saves/reports/source';dryRun=[bool]$DryRun;beforeBuilds=$taskBuildFolders.Count;kept=@($taskKeep);archive=$taskBatch;plannedBytes=($taskPlan|Measure-Object bytes -Sum).Sum;movedBytes=0L;deleted=0;records=$taskPlan;errors=@()}
if (-not $DryRun) {
 foreach ($taskRecord in $taskPlan) {
  try {
   $taskResolved = (Resolve-Path -LiteralPath $taskRecord.path).Path
   $taskRelative=$taskResolved.Substring($taskGameRoot.Length+1)
   $taskOwned=(Test-BuildFolder $taskResolved) -or $taskRelative -match '^Saved\\(?:[^\\]+\\)+UserData\\WebView2$'
   if (-not $taskResolved.StartsWith($taskGameRoot+'\',[StringComparison]::OrdinalIgnoreCase) -or -not $taskOwned -or $taskKeep.Contains($taskResolved)) { throw 'Unsafe final move path' }
   $taskDestination=[IO.Path]::GetFullPath($taskRecord.destination)
   if (-not $taskDestination.StartsWith($taskBatch+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Destination outside named quarantine batch' }
   $taskLatest=Get-ChildItem -LiteralPath $taskResolved -File -Recurse -Force|Measure-Object Length -Sum
   if ([long]$taskLatest.Sum -ne $taskRecord.bytes -or $taskLatest.Count -ne $taskRecord.files) { [void]$taskKeep.Add($taskResolved);continue }
   New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($taskDestination)) -Force|Out-Null
   Move-Item -LiteralPath $taskResolved -Destination $taskDestination
   $taskAfter=Get-ChildItem -LiteralPath $taskDestination -File -Recurse -Force|Measure-Object Length -Sum
   if ((Test-Path -LiteralPath $taskResolved) -or [long]$taskAfter.Sum -ne $taskRecord.bytes -or $taskAfter.Count -ne $taskRecord.files) { throw 'Moved contents differ from inventory' }
   $taskRecord.moved = $true
   $taskReceipt.movedBytes += $taskRecord.bytes
  } catch { $taskReceipt.errors += [pscustomobject]@{path=$taskRecord.path;error=$_.Exception.Message} }
 }
}
$taskReceipt['afterBuilds'] = @(foreach($taskPlatform in $taskPlatforms){$taskPlatformPath=Join-Path $taskBuildRoot $taskPlatform;if(Test-Path -LiteralPath $taskPlatformPath){Get-ChildItem -LiteralPath $taskPlatformPath -Directory}}).Count
$taskReceiptPath = Join-Path $taskSaved ('build-retention-'+(Get-Date -Format 'yyyyMMdd-HHmmss-fff')+'.json')
$taskReceipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $taskReceiptPath -Encoding utf8
if (-not $DryRun -and $taskPlan.Count) { New-Item -ItemType Directory -Path $taskBatch -Force | Out-Null; $taskReceipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $taskBatch '이동내역.json') -Encoding utf8 }
[pscustomobject]@{dryRun=[bool]$DryRun;beforeBuilds=$taskReceipt.beforeBuilds;afterBuilds=$taskReceipt.afterBuilds;planned=$taskPlan.Count;moved=@($taskPlan|Where-Object moved).Count;movedBytes=$taskReceipt.movedBytes;deleted=0;kept=@($taskKeep);archive=$taskBatch;errors=$taskReceipt.errors;receipt=$taskReceiptPath}|ConvertTo-Json -Depth 5
if ($taskReceipt.errors.Count) { exit 1 }
