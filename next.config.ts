import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "a.espncdn.com",
        pathname: "/combiner/i/**",
      },
      {
        protocol: "https",
        hostname: "a.espncdn.com",
        pathname: "/i/**",
      },
      {
        protocol: "https",
        hostname: "s.espncdn.com",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "media.pff.com",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "on3static.com",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "images.on3.com",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "cdn.on3.com",
        pathname: "/**",
      },
    ],
  },
};

export default nextConfig;
