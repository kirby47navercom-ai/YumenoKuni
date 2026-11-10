// A partial contour cannot become an independently sufficient answer.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {bindMineObjects} from './v4-mine-objects.mjs';
const repo=path.resolve(import.meta.dirname,'../..');
const task=JSON.parse(await fs.readFile(path.join(repo,'data/v4_story/native_tasks.json'),'utf8')).tasks['T5-MM-01'];
const selection=JSON.parse(await fs.readFile(path.join(repo,'art/v4_production/mine_objects_20261104/selection_T5-MM-01.json'),'utf8'));
const before=structuredClone(task),bank={...selection,objects:selection.objects.map(o=>({...o,hintOutline:o.id}))};
bindMineObjects(task,bank);
assert.equal(task.stage.answerRegionId,before.stage.answerRegionId);
assert.deepEqual(task.stage.regions.filter(r=>r.correct).map(r=>r.id),[before.stage.answerRegionId]);
assert.deepEqual(task.stage.regions.filter(r=>!r.correct).map(r=>r.id),before.stage.regions.filter(r=>!r.correct).map(r=>r.id));
for(const key of Object.keys(before).filter(k=>k!=='stage'))assert.deepEqual(task[key],before[key]);
const once=structuredClone(task);bindMineObjects(task,bank);assert.deepEqual(task,once);
const changed=structuredClone(before);changed.stage.regions[0].correct=false;assert.throws(()=>bindMineObjects(changed,bank));
console.log('PASS: both joins one answer, same canonical ID/wrong alternatives/queues/outcomes, idempotent, changed source rejected');
