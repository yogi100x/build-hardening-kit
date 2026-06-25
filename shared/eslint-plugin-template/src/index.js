// Rule registry. Add one require + one entry per rule.
// Referenced from eslint.config.mjs as plugins: { "@repo": <this> }.
const noRawDbClient = require("./rules/no-raw-db-client");
const noDalDisable = require("./rules/no-dal-disable");

module.exports = {
  rules: {
    "no-raw-db-client": noRawDbClient,
    "no-dal-disable": noDalDisable,
  },
};
