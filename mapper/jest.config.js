/** @type {import('jest').Config} */
const config = {
  // Default environment for pure-logic unit tests (deepEqual, constants, etc.)
  // Component tests override this with @jest-environment jsdom docblock.
  testEnvironment: "node",
  transform: {
    "^.+\\.[jt]sx?$": ["ts-jest", { tsconfig: { jsx: "react" } }],
  },
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
  },
  testMatch: ["**/*.test.ts", "**/*.test.tsx"],
  setupFilesAfterEnv: ["<rootDir>/src/test/setup.ts"],
};

module.exports = config;
