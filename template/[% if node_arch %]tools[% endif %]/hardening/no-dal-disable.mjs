// Stops the DAL rule being switched off silently. Turning it off for a line is
// allowed only with a `// DAL-EXEMPT: <reason>` comment on the line above.
// Blanket `eslint-disable` comments and inline config that turns the rule off
// (`/* eslint @hardening/no-raw-db-client: off */`) are always rejected.
const RULE = "no-raw-db-client";

export default {
  meta: {
    type: "problem",
    docs: {
      description: `Require a DAL-EXEMPT reason to disable ${RULE}; forbid blanket disables.`,
    },
    messages: {
      bareDisable: `Disabling ${RULE} requires a preceding \`// DAL-EXEMPT: <reason>\` comment.`,
      blanketDisable:
        "Bare eslint-disable suppresses every rule. Disable specific rules, with a reason.",
      configOff: `Inline config may not turn ${RULE} off. Use a DAL-EXEMPT disable on the line.`,
    },
    schema: [],
  },
  create(context) {
    const comments = context.sourceCode.getAllComments();
    return {
      Program() {
        for (const c of comments) {
          const text = c.value.trim();
          if (
            /^eslint\s/.test(text) &&
            text.includes(RULE) &&
            /:\s*["']?(off|0)\b/.test(text)
          ) {
            context.report({ loc: c.loc, messageId: "configOff" });
            continue;
          }
          const m = text.match(
            /^eslint-disable(?:-next-line|-line)?(?:\s+(.*))?$/,
          );
          if (!m) continue;
          const rules = (m[1] ?? "").split("--")[0].trim();
          if (rules === "") {
            context.report({ loc: c.loc, messageId: "blanketDisable" });
            continue;
          }
          if (rules.includes(RULE)) {
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
