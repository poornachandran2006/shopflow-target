/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    NEXT_PUBLIC_PAYMENT_API: process.env.NEXT_PUBLIC_PAYMENT_API || "http://localhost:8001",
    NEXT_PUBLIC_SENTINEL_API: process.env.NEXT_PUBLIC_SENTINEL_API || "http://localhost:8000",
  },
};

module.exports = nextConfig;
