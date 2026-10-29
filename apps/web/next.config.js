const path = require('path');
const fs = require('fs');

/**
 * When `npm run dev` runs from `apps/web`, Next only auto-loads `.env*` in this folder.
 * Merge repo-root `.env` so ADMIN_RUN_TOKEN and NEXT_PUBLIC_API_URL match the API stack.
 */
function loadEnvFromFile(filePath) {
  if (!fs.existsSync(filePath)) return;
  const txt = fs.readFileSync(filePath, 'utf8');
  for (const rawLine of txt.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith('#')) continue;
    const eq = line.indexOf('=');
    if (eq <= 0) continue;
    const key = line.slice(0, eq).trim();
    let val = line.slice(eq + 1).trim();
    if (
      (val.startsWith('"') && val.endsWith('"')) ||
      (val.startsWith("'") && val.endsWith("'"))
    ) {
      val = val.slice(1, -1);
    }
    if (process.env[key] === undefined) process.env[key] = val;
  }
}

loadEnvFromFile(path.resolve(__dirname, '..', '..', '.env'));

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async redirects() {
    return [
      { source: '/prices', destination: '/app/prices', permanent: false },
      { source: '/sufficiency', destination: '/app/sufficiency', permanent: false },
      { source: '/refineries', destination: '/app/refineries', permanent: false },
      { source: '/gas', destination: '/app/gas', permanent: false },
      { source: '/vessels', destination: '/app/vessels', permanent: false },
      { source: '/archive', destination: '/app/archive', permanent: false },
      { source: '/metadata', destination: '/app/metadata', permanent: false },
      { source: '/data-layers', destination: '/app/data-layers', permanent: false },
    ];
  },
  async rewrites() {
    // Local/Docker only: proxy helper. On Vercel Services, public rewrites in
    // root vercel.json send /v1/* (and related paths) to the FastAPI service;
    // server routes use the API_URL binding instead of this rewrite.
    const apiOrigin = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    return [
      { source: '/api/proxy/:path*', destination: `${apiOrigin}/:path*` },
    ];
  },
};

module.exports = nextConfig;
