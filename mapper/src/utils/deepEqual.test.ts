/**
 * Unit tests — src/utils/deepEqual.ts
 * Acceptance criteria.
 */
import { deepEqual } from '@/utils/deepEqual';

describe('deepEqual', () => {
    // Primitive identity
    it('returns true for identical primitives', () => {
        expect(deepEqual(1, 1)).toBe(true);
        expect(deepEqual('x', 'x')).toBe(true);
        expect(deepEqual(null, null)).toBe(true);
        expect(deepEqual(undefined, undefined)).toBe(true);
    });

    it('returns false for different primitives', () => {
        expect(deepEqual(1, 2)).toBe(false);
        expect(deepEqual('a', 'b')).toBe(false);
        expect(deepEqual(null, undefined)).toBe(false);
    });

    // KEY TEST: order-insensitive object comparison
    it('returns true for objects with same entries in different key order', () => {
        expect(deepEqual({ a: 1, b: 2 }, { b: 2, a: 1 })).toBe(true);
    });

    it('returns false for objects with different values', () => {
        expect(deepEqual({ a: 1 }, { a: 2 })).toBe(false);
    });

    it('returns false for objects with different key sets', () => {
        expect(deepEqual({ a: 1 }, { a: 1, b: 2 })).toBe(false);
    });

    // Arrays
    it('returns true for identical arrays', () => {
        expect(deepEqual([1, 2, 3], [1, 2, 3])).toBe(true);
    });

    it('returns false for arrays of different length', () => {
        expect(deepEqual([1, 2], [1, 2, 3])).toBe(false);
    });

    it('returns false for array vs object', () => {
        expect(deepEqual([1], { 0: 1 })).toBe(false);
    });

    // Nested structures
    it('returns true for deeply nested equal objects', () => {
        expect(deepEqual({ a: { b: { c: 3 } } }, { a: { b: { c: 3 } } })).toBe(true);
    });

    it('returns false for deeply nested objects with difference', () => {
        expect(deepEqual({ a: { b: 1 } }, { a: { b: 2 } })).toBe(false);
    });

    it('handles arrays of objects', () => {
        expect(deepEqual([{ id: 1 }], [{ id: 1 }])).toBe(true);
        expect(deepEqual([{ id: 1 }], [{ id: 2 }])).toBe(false);
    });

    it('returns false when one side is null', () => {
        expect(deepEqual(null, {})).toBe(false);
        expect(deepEqual({}, null)).toBe(false);
    });
});

