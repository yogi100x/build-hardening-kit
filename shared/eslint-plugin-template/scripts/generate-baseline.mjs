// Snapshots current raw DB-client calls per file into the baseline JSON.
// Run once to seed, then re-run after fixing debt to lock in the lower number.
// Approximate (regex) — the ESLint rule's AST pass is the source of truth.
import fs from "node:fs";
import path from "node:path";

const ROOTS = ["src", "apps", "packages"];
const EXT = new Set([".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"]);
const PATTERN = /\b(supabase|client|db|adminClient|prisma|knex)\.(from|query|rawQuery)\s*\(/g;
const OUT = "packages/eslint-plugin/src/baselines/raw-db-from.json";

const baseline = {};

function walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (
      entry.name === "node_modules" ||
      entry.name === "dist" ||
      entry.name === "build" ||
      entry.name.startsWith(".")
    )
      continue;
    const p = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      walk(p);
    } else if (EXT.has(path.extname(entry.name))) {
      const rel = path.relative(process.cwd(), p).split(path.sep).join("/");
      if (/(^|\/)(dal|data-access)\//.test(rel)) continue;
      const src = fs.readFileSync(p, "utf8");
      const n = (src.match(PATTERN) || []).length;
      if (n > 0) baseline[rel] = n;
    }
  }
}

for (const r of ROOTS) if (fs.existsSync(r)) walk(r);

fs.mkdirSync(path.dirname(OUT), { recursive: true });
fs.writeFileSync(OUT, JSON.stringify(baseline, null, 2) + "\n");

const files = Object.keys(baseline).length;
const total = Object.values(baseline).reduce((a, b) => a + b, 0);
console.log(`wrote ${OUT}: ${files} files, ${total} raw calls`);
