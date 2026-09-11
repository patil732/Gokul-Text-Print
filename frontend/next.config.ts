import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async redirects() {
    return [
      {
        source: "/dashboard/sales",
        destination: "/sales",
        permanent: true,
      },
      {
        source: "/dashboard/inventory",
        destination: "/inventory",
        permanent: true,
      },
      {
        source: "/dashboard/copilot",
        destination: "/copilot",
        permanent: true,
      },
      {
        source: "/dashboard/knowledge",
        destination: "/knowledge",
        permanent: true,
      },
      {
        source: "/dashboard/reports",
        destination: "/reports",
        permanent: true,
      },
      {
        source: "/dashboard/alerts",
        destination: "/alerts",
        permanent: true,
      },
      {
        source: "/dashboard/settings",
        destination: "/settings",
        permanent: true,
      },
    ];
  },
};

export default nextConfig;
