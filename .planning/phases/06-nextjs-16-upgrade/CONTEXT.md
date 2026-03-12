# Context: Phase 6 - Next.js 16 Upgrade

## Domain Boundary
Upgrading the `mapper` frontend from Next.js 15 to Next.js 16 to leverage Turbopack, Cache Components, and the new `proxy.ts` architecture while maintaining integration with AG UI and CopilotKit.

## Implementation Decisions

### 1. Infrastructure Strategy
- **Decision**: Prioritize **Turbopack** as the default bundler for development and production.
- **Rationale**: Maximize performance gains.
- **Contingency**: If specific build errors arise, they will be analyzed on a case-by-case basis before considering a Webpack fallback.

### 2. API & Parameter Migration
- **Decision**: Use **automated codemods** (`@next/codemod@canary`) for initial migration of synchronous request APIs (params/searchParams).
- **Fallback**: If automated migration is incomplete or causes type errors, perform a manual **file-by-file review** to ensure TypeScript safety.

### 3. Dependency Management (CopilotKit)
- **Decision**: If **CopilotKit** or other core dependencies exhibit regressions or incompatibility with Next.js 16, **defer the upgrade** for that specific component/route rather than applying local patches.
- **Rationale**: Maintain long-term upstream compatibility and avoid maintainability debt through local patches.

### 4. Architectural Shift (proxy.ts)
- **Decision**: Proactively migrate existing API routing and middleware patterns to the new **`proxy.ts`** system introduced in Next.js 16.

## Claude's Discretion
- Identifying and resolving minor CSS/UI regressions caused by the React Compiler or Turbopack.
- Determining the most efficient path for TypeScript type updates during the manual review phase.

## Specific Ideas/References
- Automated Upgrade CLI: `npx @next/codemod@canary upgrade latest`
- Asynchronous Request APIs: [Next.js Documentation](https://nextjs.org/docs/app/building-your-application/upgrading/version-16#asynchronous-request-apis)

## Deferred Ideas
- Local patching of 3rd party libraries (opted for deferral instead).
- Full rewrite of data-fetching hooks (out of scope for framework upgrade).
