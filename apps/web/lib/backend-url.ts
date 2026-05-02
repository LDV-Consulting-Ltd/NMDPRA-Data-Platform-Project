/**
 * FastAPI base URL for Next.js **server** routes only.
 * Evaluated at request time so env is available after `next.config.js` loads monorepo `.env`.
 */
export function backendApiBase(): string {
  return (
    process.env.BACKEND_API_URL ||
    process.env.API_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    'http://localhost:8000'
  );
}
