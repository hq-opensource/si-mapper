import type { Metadata } from "next";

import "./globals.css";
import "@copilotkit/react-ui/styles.css";
import { AppIconsContextProvider } from "@/lib/app-icons-context";
import { WorkspaceProvider } from "@/context/WorkspaceContext";
import { CopilotKitWrapper } from "@/components/CopilotKitWrapper";

export const metadata: Metadata = {
  title: "SI-MAPPER",
  description: "Open Source software by Hydro-Quebec.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="light">
      <body className={"antialiased"}>
        {/*
          WorkspaceProvider must be OUTSIDE CopilotKit so that CopilotKitWrapper
          can read activeSession and pass threadId to CopilotKit. This is what
          makes the agent backend route each CopilotKit request to the correct
          ADK session (matched by _ag_ui_thread_id == session_id in SQLite).
        */}
        <WorkspaceProvider>
          <CopilotKitWrapper>
            <AppIconsContextProvider>
              {children}
            </AppIconsContextProvider>
          </CopilotKitWrapper>
        </WorkspaceProvider>
      </body>
    </html>
  );
}
