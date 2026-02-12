"use client";

interface ExternalPageIframeProps {
  src: string;
  width?: string;
  height?: string;
}

export function ExternalPageIframe({ src, width = "100%", height = "100%", className = "" }: ExternalPageIframeProps & { className?: string }) {
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