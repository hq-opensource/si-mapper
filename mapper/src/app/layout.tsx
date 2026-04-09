import type { Metadata } from "next";

import { CopilotKit } from "@copilotkit/react-core";
import "./globals.css";
import "@copilotkit/react-ui/styles.css";
import { AppIconsContextProvider } from "@/lib/app-icons-context";
import { WorkspaceProvider } from "@/context/WorkspaceContext";

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
        <CopilotKit runtimeUrl="/api/copilotkit" agent="my_agent" showDevConsole={false}>
          <AppIconsContextProvider>
            <WorkspaceProvider>
              {children}
            </WorkspaceProvider>
          </AppIconsContextProvider>
        </CopilotKit>
      </body>
    </html>
  );
}
