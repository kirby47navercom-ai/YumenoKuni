// Recover evidence of a traversal whose final report writer failed. Never rewrites
// the failed run's failure.json or labels its process exit as successful.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
const [runArg,restoreArg]=process.argv.slice(2);assert(runArg&&restoreArg,'usage: run-directory fresh-entry-report');
const run=path.resolve(runArg),restorePath=path.resolve(restoreArg),read=p=>fs.readFile(p,'utf8').then(JSON.parse);
const failure=await read(path.join(run,'failure.json')),visited=await read(path.join(run,'visited.json')),restore=await read(restorePath);
assert.match(failure.error,/^ReferenceError: s is not defined/);assert.deepEqual(failure.probeErrors,[]);assert(restore.ok&&restore.entryOnly);assert.equal(path.resolve(restore.resume),path.join(run,'chapter-'+restore.chapter+'-savegames.json'));
const bytes=await fs.readFile(restore.resume),raw=JSON.parse(bytes),item=Object.entries(raw.items).find(([key])=>key.includes('yumeno-progress-v4.project.'));assert(item);const saved=JSON.parse(item[1]);assert.equal(saved.node,restore.node);assert.equal(Number(saved.chapter),restore.chapter);
assert(visited.chapters.length>0&&visited.chapters.every(c=>c<restore.chapter));assert.equal(failure.results.length,visited.tasks.length);assert(failure.results.every(r=>r.outcome.taskId===r.taskId));assert.deepEqual([...new Set(failure.results.map(r=>r.taskId))].sort(),[...visited.tasks].sort());
const report={recoveryValidationPassed:true,originalHarnessRunPassed:false,originalFailure:failure.error.split('\n')[0],run,freshRestoreReport:restorePath,endedAtChapter:restore.chapter,endedAtNode:restore.node,persistedSaveSha256:createHash('sha256').update(bytes).digest('hex'),traversedChapters:visited.chapters,visitedNodes:visited.nodes.length,resolvedTasks:failure.results.length,results:failure.results,scope:'Recovered normal-route evidence: every recorded real-input task has its authored outcome, the persisted next-chapter checkpoint exists and a fresh native player restored its exact head. The original final report writer failed; failure.json remains. Not all branches, full campaign, play duration, visual or hearing acceptance.'};
await fs.writeFile(path.join(run,'range-evidence-recovery.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({recoveryValidationPassed:true,originalHarnessRunPassed:false,run,resolvedTasks:report.resolvedTasks,endedAtChapter:restore.chapter}));
