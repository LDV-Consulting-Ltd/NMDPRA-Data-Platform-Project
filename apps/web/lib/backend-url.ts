/**
 * FastAPI base URL for Next.js **server** routes / Server Components only.
 *
 * On Vercel Services, `API_URL` is injected by a service binding (web → api).
 * Do not set `API_URL` yourself in the Vercel project when using bindings.
 * Bindings resolve at runtime in functions — not during builds or middleware.
 *
 * Local / Docker: API_URL or BACKEND_API_URL (e.g. http://api:8000).
 * Browser clients should use same-origin public paths (/v1/..., /health) or NEXT_PUBLIC_API_URL.
 */
export function backendApiBase(): string {
  const base =
    process.env.API_URL ||
    process.env.BACKEND_API_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    'http://localhost:8000';
  return base.replace(/\/$/, '');
}
