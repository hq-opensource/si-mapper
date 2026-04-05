/**
 * Global Jest setup — applied to every test suite.
 * Minimal: only @testing-library/jest-dom matchers.
 * MSW server lifecycle is managed per-test-file where needed.
 */
import '@testing-library/jest-dom';
