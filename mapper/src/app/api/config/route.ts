/**
 * GET /api/config
 * ─────────────────────────────────────────────────────────────────────────────
 * Returns public deployment configuration consumed by client components.
 *
 * - graphivacBaseUrl  — browser-reachable base URL of the Graphivac service.
 *                       Reads GRAPHIVAC_PUBLIC_BASE_URL first; falls back to
 *                       GRAPHIVAC_BASE_URL so single-var cloud deployments work
 *                       without any config change.
 * - graphivacOrgId   — the organisation ID for this deployment (e.g. "public")
 *
 * Why two Graphivac URL vars?
 * In Docker the server-to-server call uses the container DNS name
 * (GRAPHIVAC_BASE_URL=http://graphivac:3000) while the browser must use the
 * host-exposed address (GRAPHIVAC_PUBLIC_BASE_URL=http://localhost:3000).
 * For cloud deployments both are the same, so only GRAPHIVAC_BASE_URL is needed.
 *
 * These values are exposed here (rather than NEXT_PUBLIC_ env vars) so that:
 * 1. They remain consistent with the server-side graphivac-client.ts.
 * 2. They are not baked in at build time — useful for containerised deployments.
 *
 * Neither value is secret: both already appear in Graphivac iframe URLs.
 */

import { NextResponse } from 'next/server';

export async function GET(): Promise<NextResponse> {
  return NextResponse.json({
    graphivacBaseUrl: process.env.GRAPHIVAC_PUBLIC_BASE_URL
      ?? process.env.GRAPHIVAC_BASE_URL
      ?? '',
    graphivacOrgId: process.env.GRAPHIVAC_ORG_ID ?? '',
  });
}



