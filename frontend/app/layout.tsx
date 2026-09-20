import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/components/auth-provider";
import { ProtectedApp } from "@/components/protected-app";
export const metadata: Metadata = {
  title: "SalesOps AI",
  description: "AI-Powered Lead Qualification & Sales Automation",
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <ProtectedApp>{children}</ProtectedApp>
        </AuthProvider>
      </body>
    </html>
  );
}
