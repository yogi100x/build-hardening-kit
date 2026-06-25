// TypeScript variant. Type-checked lint rules + custom plugin.
import js from "@eslint/js";
import tseslint from "typescript-eslint";
import repo from "@repo/eslint-plugin";

export default tseslint.config(
  { ignores: ["dist", "build", ".next", "coverage", "**/*.config.*"] },
  js.configs.recommended,
  ...tseslint.configs.recommendedTypeChecked,
  {
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
    plugins: { "@repo": repo },
    rules: {
      "@repo/no-raw-db-client": "error",
      "@repo/no-dal-disable": "error",
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],
      "@typescript-eslint/no-floating-promises": "error",
      "@typescript-eslint/await-thenable": "error",
      eqeqeq: ["error", "always"],
      "prefer-const": "error",
      "no-console": ["warn", { allow: ["warn", "error"] }],
    },
  },
);
