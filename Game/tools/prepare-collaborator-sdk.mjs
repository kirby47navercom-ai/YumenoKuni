import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';

assert(process.platform === 'win32' && process.arch === 'x64', 'Windows x64 is required');
const parent = await fs.realpath(path.resolve(import.meta.dirname, '..'));
const target = path.join(parent, 'engineCreate');
const inputs = path.join(import.meta.dirname, 'collaborator-sdk');
const lock = JSON.parse(await fs.readFile(path.join(inputs, 'lock.json'), 'utf8'));
const marker = '.yumeno-build-sdk.json';
const archive = path.join(inputs, 'hbengine-compat.tar.gz');
const source = path.join(inputs, 'hbengine-source.tar.gz');
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const exists = file => fs.stat(file).then(() => true, error => {
  if (error.code === 'ENOENT') return false;
  throw error;
});

if (await exists(target)) {
  const prepared = await fs.readFile(path.join(target, marker), 'utf8')
    .then(JSON.parse, error => {
      if (error.code === 'ENOENT') return null;
      throw error;
    });
  if (prepared?.sourceSha256 === lock.sourceSha256 &&
      prepared.overlaySha256 === lock.overlaySha256 &&
      hash(await fs.readFile(path.join(target, 'HBNativePlayer.exe'))) === lock.playerSha256) {
    console.log(target);
    process.exit(0);
  }
  throw Error('Existing engineCreate is owned by another checkout or SDK version: ' + target);
}

assert.equal(hash(await fs.readFile(archive)), lock.overlaySha256);
assert.equal(hash(await fs.readFile(source)), lock.sourceSha256);
const scratch = await fs.mkdtemp(path.join(parent, '.yumeno-engine-'));
const run = (file, args) => execFileSync(file, args, {cwd: scratch, windowsHide: true, stdio: 'inherit'});
try {
  run('tar.exe', ['-xf', source]);
  run(process.execPath, [path.join(path.dirname(process.execPath), 'node_modules/npm/bin/npm-cli.js'), 'ci', '--no-audit', '--no-fund']);
  run('tar.exe', ['-xf', archive]);
  assert.equal(hash(await fs.readFile(path.join(scratch, 'HBNativePlayer.exe'))), lock.playerSha256);
  await fs.writeFile(path.join(scratch, marker), JSON.stringify(lock) + '\n');
  await fs.rename(scratch, target);
} finally {
  if (await exists(scratch)) {
    const resolved = await fs.realpath(scratch);
    assert.equal(path.dirname(resolved), parent);
    assert(path.basename(resolved).startsWith('.yumeno-engine-'));
    await fs.rm(resolved, {recursive: true, force: true});
  }
}
console.log(target);
