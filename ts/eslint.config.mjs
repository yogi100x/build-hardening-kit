// TypeScript variant. Type-checked rules apply to TypeScript files only; plain
// JS (the kit's lint plugin, Node scripts) gets the untyped rules.
import js from "@eslint/js";
import globals from "globals";
import tseslint from "typescript-eslint";
import repo from "@repo/eslint-plugin";

export default tseslint.config(
  { ignores: ["dist", "build", ".next", "coverage", "**/*.config.*"] },
  js.configs.recommended,
  {
    files: ["**/*.{ts,tsx,mts,cts}"],
    extends: [tseslint.configs.recommendedTypeChecked],
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
    rules: {
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],
      "@typescript-eslint/no-floating-promises": "error",
      "@typescript-eslint/await-thenable": "error",
    },
  },
  {
    plugins: { "@repo": repo },
    rules: {
      "@repo/no-raw-db-client": "error",
      "@repo/no-dal-disable": "error",
      eqeqeq: ["error", "always"],
      "prefer-const": "error",
      "no-console": ["warn", { allow: ["warn", "error"] }],
    },
  },
  {
    // Node-run JS: the kit's plugin (CommonJS) and its scripts.
    files: ["**/*.{js,mjs,cjs}"],
    languageOptions: { globals: globals.node },
  },
  {
    files: ["packages/eslint-plugin/**/*.js"],
    languageOptions: { sourceType: "commonjs" },
  },
  {
    files: ["packages/eslint-plugin/scripts/**"],
    rules: { "no-console": "off" },
  },
);
