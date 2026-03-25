"use client";

interface ExternalPageIframeProps {
  src: string;
  width?: string;
  height?: string;
}

export function ExternalPageIframe({ src, width = "100%", height = "100%", className = "" }: ExternalPageIframeProps & { className?: string }) {
  if (!src) {
    return (
      <div
        className={`w-full h-full min-h-[700px] flex flex-col items-center justify-center gap-4 bg-[var(--background)] text-[var(--muted-foreground)] ${className}`}
        style={{ width, height }}
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="opacity-40">
          <rect x="3" y="3" width="18" height="18" rx="2" />
          <path d="M3 9h18M9 21V9" />
        </svg>
        <p className="text-sm font-medium opacity-60">No grid URL configured</p>
        <p className="text-xs opacity-40 max-w-xs text-center">
          Set <code className="font-mono bg-[var(--muted)]/30 px-1 rounded">NEXT_PUBLIC_GRAPHIVAC_GRID_URL</code> in your <code className="font-mono bg-[var(--muted)]/30 px-1 rounded">.env.local</code> to display the Graphivac grid here.
        </p>
      </div>
    );
  }

  return (
    <iframe
      src={src}
      width={width}
      height={height}
      className={`w-full h-full min-h-[700px] ${className}`}
      style={{ border: "none" }}
      title="External Webpage"
    ></iframe>
  );
}

