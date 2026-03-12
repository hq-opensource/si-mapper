# Plan 6: Next.js 16 Upgrade

**Goal:** Upgrade the `mapper` frontend to Next.js 16 to leverage performance improvements (Turbopack, Cache Components) and ensure long-term maintainability.

## 1. Environment & Dependency Preparation
- [ ] **Check Node.js Version**: Ensure Node.js is >= 20.9.
- [ ] **Check TypeScript Version**: Ensure TypeScript is >= 5.1.
- [ ] **Research CopilotKit Compatibility**: Verify if `@copilotkit/react-core@1.10.6` supports Next.js 16 or if an upgrade is required.
- [ ] **Backup/Branch**: Create a new git branch `feature/nextjs-16-upgrade`.

## 2. Upgrade Execution
- [ ] **Run Codemod**: 
  ```bash
  npx @next/codemod@canary upgrade latest
  ```
- [ ] **Manual Update**: If codemod fails to update dependencies:
  ```bash
  pnpm install next@latest react@latest react-dom@latest
  ```
- [ ] **Update Type Definitions**:
  ```bash
  pnpm install -D @types/node@latest @types/react@latest @types/react-dom@latest
  ```

## 3. Handling Breaking Changes
- [ ] **Asynchronous Request APIs**:
  - Run automated codemods first.
  - Perform **file-by-file manual review** of `src/app/page.tsx` and routes for Promise-based params.
- [ ] **`proxy.ts` System**:
  - Proactively migrate API routing and any pseudo-middleware to the new `proxy.ts`.
- [ ] **Turbopack Priority**:
  - Enable Turbopack by default. If regressions occur, debug before falling back to Webpack.
- [ ] **Dependency Failure Handling**:
  - If **CopilotKit** or core UI libraries fail build/runtime, **defer the upgrade** for that component rather than patching.

## 4. Validation & Testing
- [ ] **Clean Install**: Delete `node_modules` and re-install to ensure clean dependencies.
- [ ] **Build Check**:
  ```bash
  pnpm run build
  ```
- [ ] **Runtime Verification**:
  - Start the app with `pnpm run dev`.
  - Verify AG UI components (`@ag-ui/client`) work correctly.
  - Verify CopilotKit integration (HUD and input) remains functional.
  - Test multi-model agent selection and output rendering.

## 5. Metadata Integration
- [ ] Update `ROADMAP.md` and `STATE.md` completion markers once verified.
