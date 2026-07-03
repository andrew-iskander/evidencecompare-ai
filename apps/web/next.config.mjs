/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Emit a minimal standalone server bundle for the Docker runtime image.
  output: "standalone",
};

export default nextConfig;
