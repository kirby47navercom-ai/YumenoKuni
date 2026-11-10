import path from 'node:path';
import { spawnSync } from 'node:child_process';

const root = path.resolve(import.meta.dirname, '..');
for (const args of [
  ['tools/prepare-collaborator-sdk.mjs'],
  ['tools/create-project.mjs', '--revised-campaign'],
  ['tools/build.mjs', ...process.argv.slice(2)],
]) {
  const result = spawnSync(process.execPath, args, {cwd: root, windowsHide: true, stdio: 'inherit'});
  if (result.error) throw result.error;
  if (result.status !== 0) process.exit(result.status ?? 1);
}
