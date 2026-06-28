/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  distDir: process.env.NEXT_DIST_DIR || '.next',
  experimental: {
    // Next.js 16.2 defaults lockDistDir to true, which prevents a second
    // `next dev` in the same project. Set to false to allow multiple servers.
    lockDistDir: false
  }
};

export default nextConfig;
