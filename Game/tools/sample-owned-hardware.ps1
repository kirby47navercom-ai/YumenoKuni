param([int]$RootProcessId,[int]$Seconds=30,[Parameter(Mandatory=$true)][string]$OutputPath)
$ErrorActionPreference='Stop'
if($RootProcessId -le 0 -or $Seconds -lt 10 -or $Seconds -gt 60){throw 'Invalid owned sample bounds'}
$taskRoot=Get-Process -Id $RootProcessId
if($taskRoot.ProcessName -notlike 'HBGame*'){throw 'Expected owned HBGame root'}
$taskIds=@($RootProcessId)
$taskFront=@($RootProcessId)
while($taskFront.Count){
 $taskNext=@()
 foreach($taskParent in $taskFront){foreach($taskChild in @(Get-CimInstance Win32_Process -Filter "ParentProcessId=$taskParent")){
  if([int]$taskChild.ProcessId -notin $taskIds){$taskIds+=([int]$taskChild.ProcessId);$taskNext+=([int]$taskChild.ProcessId)}
 }}
 $taskFront=$taskNext
}
$taskRows=@();$taskLast=@{};$taskStarted=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
while(([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()-$taskStarted) -lt $Seconds*1000){
 $taskProcesses=@()
 foreach($taskId in $taskIds){
  $taskProcess=Get-Process -Id $taskId -ErrorAction SilentlyContinue
  if(-not $taskProcess){continue}
  $taskTime=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();$taskCPU=$taskProcess.TotalProcessorTime.TotalMilliseconds
  $taskPrior=$taskLast[$taskId];$taskCores=$null
  if($taskPrior -and $taskTime -gt $taskPrior.time){$taskCores=($taskCPU-$taskPrior.cpuMS)/($taskTime-$taskPrior.time)}
  $taskLast[$taskId]=@{time=$taskTime;cpuMS=$taskCPU}
  $taskProcesses+=@{pid=$taskId;name=$taskProcess.ProcessName;time=$taskTime;cpuMS=$taskCPU;cpuCoreEquivalents=$taskCores}
 }
 $taskGPU=@(Get-CimInstance Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine -Filter "Name LIKE 'pid_$($RootProcessId)_%'"|ForEach-Object{
  @{name=$_.Name;utilization=[double]$_.UtilizationPercentage;runningTime=[string]$_.RunningTime;timestamp=[string]$_.Timestamp_Sys100NS}
 })
 $taskRows+=@{time=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();processes=$taskProcesses;gpu=$taskGPU}
 Start-Sleep -Milliseconds 900
}
if($taskRows.Count -lt 3 -or -not @($taskRows|Where-Object{$_.gpu.Count}).Count){throw 'Insufficient live GPU counter samples'}
@{rootPid=$RootProcessId;descendantPids=$taskIds;started=$taskStarted;ended=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();samples=$taskRows;scope='Read-only Windows per-process counters for this owned HBGame and its launch descendants. CPU core equivalents are CPU time / wall time (1 = one fully occupied logical core), not machine CPU percentage. GPU percentages are individual engine counters; do not add overlapping engines. External sampling overhead: diagnostic, not normal FPS acceptance.'}|ConvertTo-Json -Depth 9|Set-Content -LiteralPath $OutputPath -Encoding utf8
