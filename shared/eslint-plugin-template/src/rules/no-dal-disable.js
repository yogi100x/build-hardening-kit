// Stops people from silently turning off the DAL rule.
// A disable of no-raw-db-client is allowed ONLY when the line above carries a
// `// DAL-EXEMPT: <reason>` comment. Bare blanket disables are always rejected.
module.exports = {
  meta: {
    type: "problem",
    docs: {
      description:
        "Require a // DAL-EXEMPT: <reason> when disabling no-raw-db-client; forbid blanket disables.",
    },
    messages: {
      bareDisable:
        "Disabling no-raw-db-client requires a preceding `// DAL-EXEMPT: <reason>` comment.",
      blanketDisable:
        "Bare eslint-disable suppresses every rule. Disable specific rules, with a reason.",
    },
    schema: [],
  },
  create(context) {
    const sc = context.sourceCode ?? context.getSourceCode();
    return {
      Program() {
        const comments = sc.getAllComments();
        for (const c of comments) {
          const text = c.value.trim();
          const m = text.match(/^eslint-disable(?:-next-line|-line)?\s*(.*)$/);
          if (!m) continue;
          const rules = m[1].trim();
          if (rules === "") {
            context.report({ loc: c.loc, messageId: "blanketDisable" });
            continue;
          }
          if (/no-raw-db-client/.test(rules)) {
            const hasReason = comments.some(
              (o) =>
                o.loc.end.line === c.loc.start.line - 1 &&
                /DAL-EXEMPT:/.test(o.value),
            );
            if (!hasReason)
              context.report({ loc: c.loc, messageId: "bareDisable" });
          }
        }
      },
    };
  },
};
