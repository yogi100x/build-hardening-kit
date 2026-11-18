// Example custom rule + baseline-ratchet.
// Flags raw DB-client calls (client.from(...), db.query(...)) outside the data-access layer.
// Only reports violations BEYOND the per-file count recorded in the baseline, so existing
// debt passes and only NEW raw calls fail. Drive the baseline to zero over time.
//
// Adapt this for YOUR footgun: rename the rule, change CLIENT_NAMES + METHODS, or replace
// the whole detection (raw fetch, console.log, deep imports — anything AST-detectable).
const path = require("path");

const CLIENT_NAMES = new Set([
  "supabase",
  "client",
  "db",
  "adminClient",
  "prisma",
  "knex",
]);
const METHODS = new Set(["from", "query", "rawQuery"]);
// Prisma is matched on any call: prisma.$queryRaw(...) and model calls like
// prisma.user.findMany(...).
const PRISMA = "prisma";
// Keep in step with DAL_POLICY.md and semgrep/rules.yml.
const DAL_DIR = /(^|\/)(dal|data-access|data_access)\//;

let baseline = {};
try {
  baseline = require("../baselines/raw-db-from.json");
} catch {
  baseline = {};
}

function relPath(filename) {
  return path.relative(process.cwd(), filename).split(path.sep).join("/");
}

module.exports = {
  meta: {
    type: "problem",
    docs: {
      description:
        "Disallow raw DB-client calls outside the DAL (baseline-ratcheted).",
    },
    messages: {
      rawDbCall:
        "Raw DB call outside the data-access layer. Move it into a DAL function. (exceeds baseline)",
    },
    schema: [],
  },
  create(context) {
    const rel = relPath(context.getFilename());
    // The DAL itself is allowed to talk to the client directly.
    if (DAL_DIR.test(rel)) return {};

    const allowed = baseline[rel] || 0;
    const found = [];

    return {
      CallExpression(node) {
        const callee = node.callee;
        if (callee.type !== "MemberExpression") return;
        const obj = callee.object;

        const isPrisma =
          (obj.type === "Identifier" && obj.name === PRISMA) ||
          (obj.type === "MemberExpression" &&
            obj.object.type === "Identifier" &&
            obj.object.name === PRISMA);
        if (isPrisma) {
          found.push(node);
          return;
        }

        const prop = callee.property;
        if (prop.type !== "Identifier" || !METHODS.has(prop.name)) return;

        const objName =
          obj.type === "Identifier"
            ? obj.name
            : obj.type === "MemberExpression" &&
                obj.property.type === "Identifier"
              ? obj.property.name
              : null;

        if (objName && CLIENT_NAMES.has(objName)) found.push(node);
      },
      "Program:exit"() {
        // Reports only the calls beyond the allowed baseline count for this file.
        found.forEach((node, i) => {
          if (i >= allowed) context.report({ node, messageId: "rawDbCall" });
        });
      },
    };
  },
};
