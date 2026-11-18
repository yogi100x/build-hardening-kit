// The kit's example architecture rules, as a local ESLint plugin.
import noDalDisable from "./no-dal-disable.mjs";
import noRawDbClient from "./no-raw-db-client.mjs";

export default {
  meta: { name: "hardening" },
  rules: {
    "no-raw-db-client": noRawDbClient,
    "no-dal-disable": noDalDisable,
  },
};
