import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Expose the API base URL to both server and client components
  env: {
    API_URL: process.env.API_URL ?? "http://localhost:8000",
  },
};

export default nextConfig;
