import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/backend/device/:path*",
        destination: "http://localhost:8000/:path*",
      },
      {
        source: "/backend/data/:path*",
        destination: "http://localhost:8081/:path*",
      },
      {
        source: "/backend/rule-engine/:path*",
        destination: "http://localhost:8002/:path*",
      },

      // analytics-service
      {
        source: "/backend/analytics/:path*",
        destination: "http://localhost:8003/:path*",
      },

      // ✅ data-export-service  (THIS WAS MISSING)
      {
        source: "/backend/data-export/:path*",
        destination: "http://localhost:8080/:path*",
      },
    ];
  },
};

export default nextConfig;