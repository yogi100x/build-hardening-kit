// Plain-JS variant. Re-enables the checks TypeScript would otherwise make redundant.
import js from "@eslint/js";
import globals from "globals";
import repo from "@repo/eslint-plugin";

export default [
  { ignores: ["dist", "build", ".next", "coverage", "**/*.config.*"] },
  js.configs.recommended,
  {
    languageOptions: {
      ecmaVersion: 2023,
      sourceType: "module",
      globals: { ...globals.node, ...globals.browser },
    },
    plugins: { "@repo": repo },
    rules: {
      "@repo/no-raw-db-client": "error",
      "@repo/no-dal-disable": "error",
      "no-undef": "error",
      "no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
      "no-shadow": "error",
      "consistent-return": "error",
      "no-implicit-coercion": "error",
      eqeqeq: ["error", "always"],
      "prefer-const": "error",
      "no-var": "error",
      "no-console": ["warn", { allow: ["warn", "error"] }],
    },
  },
];
