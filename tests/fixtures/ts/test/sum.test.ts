import assert from "node:assert/strict";
import { test } from "node:test";

// A TypeScript test using node:test: must pass lint (no-floating-promises
// knows test() is awaited by the runner) and the type check (@types/node).
test("adds", () => {
  assert.equal(1 + 1, 2);
});
