import { readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

const DIST_ASSETS_DIR = join(process.cwd(), 'dist/assets');
const MAX_JS_CHUNK_BYTES = 500 * 1024;

const jsAssets = readdirSync(DIST_ASSETS_DIR)
  .filter((fileName) => fileName.endsWith('.js'))
  .map((fileName) => {
    const path = join(DIST_ASSETS_DIR, fileName);
    return { fileName, bytes: statSync(path).size };
  })
  .sort((left, right) => right.bytes - left.bytes);

const oversized = jsAssets.filter((asset) => asset.bytes > MAX_JS_CHUNK_BYTES);

for (const asset of jsAssets) {
  const kb = (asset.bytes / 1024).toFixed(2);
  console.log(`${asset.fileName}: ${kb} kB`);
}

if (oversized.length > 0) {
  const limitKb = (MAX_JS_CHUNK_BYTES / 1024).toFixed(0);
  console.error(`JS chunk size check failed: ${oversized.length} file(s) exceed ${limitKb} kB.`);
  process.exitCode = 1;
}
