import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  experimental: { workerThreads: true },
  // CI normally checks types inside the build. Restricted runners can opt out
  // only after running the dedicated strict `npm run typecheck` command.
  typescript: { ignoreBuildErrors: process.env.NEXT_SKIP_TYPECHECK === "true" },
};

export default nextConfig;
