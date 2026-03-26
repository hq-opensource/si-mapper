/**
 * GET /api/config
 * ─────────────────────────────────────────────────────────────────────────────
 * Returns public deployment configuration consumed by client components.
 *
 * - graphivacBaseUrl  — base URL of the Graphivac service (e.g. "https://graphivac.hvac.io")
 * - graphivacOrgId   — the organisation ID for this deployment (e.g. "public")
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
    graphivacBaseUrl: process.env.GRAPHIVAC_BASE_URL ?? '',
    graphivacOrgId: process.env.GRAPHIVAC_ORG_ID ?? '',
  });
}

