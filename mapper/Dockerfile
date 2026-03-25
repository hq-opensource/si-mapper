# ── Stage 1: Install dependencies ──────────────────────────────────────────
FROM node:20-alpine AS deps
RUN corepack enable && corepack prepare pnpm@latest --activate
WORKDIR /app
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
# --ignore-scripts skips the postinstall hook that syncs Python/uv environments
# (agent and MCP server run in separate containers)
RUN pnpm install --frozen-lockfile --ignore-scripts

# ── Stage 2: Build ──────────────────────────────────────────────────────────
FROM node:20-alpine AS builder
RUN corepack enable && corepack prepare pnpm@latest --activate
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1

# NEXT_PUBLIC_* vars are inlined at build time by the Next.js compiler.
# They must be declared as ARGs and promoted to ENVs before `pnpm build` runs.
# Pass them via `docker compose build --build-arg` or the `args:` block in docker-compose.yml.
ARG NEXT_PUBLIC_AGENT_BACKEND_URL
ARG NEXT_PUBLIC_GRAPHIVAC_GRID_URL
ENV NEXT_PUBLIC_AGENT_BACKEND_URL=$NEXT_PUBLIC_AGENT_BACKEND_URL
ENV NEXT_PUBLIC_GRAPHIVAC_GRID_URL=$NEXT_PUBLIC_GRAPHIVAC_GRID_URL

RUN pnpm build

# ── Stage 3: Runtime image ──────────────────────────────────────────────────
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Standalone output bundles only the files needed at runtime
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

# uploads/ will be mounted as a Docker volume — create the mount point
RUN mkdir -p /app/uploads

EXPOSE 3000
CMD ["node", "server.js"]

