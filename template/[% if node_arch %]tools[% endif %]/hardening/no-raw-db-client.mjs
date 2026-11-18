// Flags raw DB-client calls (db.query(...), supabase.from(...), any prisma call)
// outside the data-access layer. Existing calls are recorded with ESLint's own
// suppressions (`npx eslint --suppress-all .`), not by this rule.
//
// Adapt it to your footgun: rename it, change CLIENT_NAMES / METHODS, or replace
// the detection (raw fetch, console.log, deep imports — anything in the AST).

const CLIENT_NAMES = new Set([
  "supabase",
  "client",
  "db",
  "adminClient",
  "knex",
]);
const METHODS = new Set(["from", "query", "rawQuery"]);
// Prisma is matched on any call: prisma.$queryRaw(...), prisma.user.findMany(...).
const PRISMA = "prisma";
// Keep in step with .semgrep/hardening.yml and the kit's DAL policy.
const DAL_DIR = /(^|\/)(dal|data-access|data_access)\//;

function memberName(node) {
  if (node.type === "Identifier") return node.name;
  if (node.type === "MemberExpression" && node.property.type === "Identifier") {
    return node.property.name;
  }
  return null;
}

export default {
  meta: {
    type: "problem",
    docs: {
      description:
        "Disallow raw DB-client calls outside the data-access layer.",
    },
    messages: {
      rawDbCall:
        "Raw DB call outside the data-access layer. Move it into a DAL function.",
    },
    schema: [],
  },
  create(context) {
    const file = context.filename.split("\\").join("/");
    if (DAL_DIR.test(file)) return {};
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
        const isClientCall =
          callee.property.type === "Identifier" &&
          METHODS.has(callee.property.name) &&
          CLIENT_NAMES.has(memberName(obj) ?? "");
        if (isPrisma || isClientCall)
          context.report({ node, messageId: "rawDbCall" });
      },
    };
  },
};
