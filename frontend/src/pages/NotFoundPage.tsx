import { Link } from 'react-router-dom';

export function NotFoundPage() {
  return (
    <div className="grid min-h-[60vh] place-items-center text-center">
      <div>
        <p className="text-6xl font-bold text-primary-500">404</p>
        <h1 className="mt-2 text-xl font-semibold">Page not found</h1>
        <p className="mt-1 text-sm text-ink-muted">
          The page you’re looking for doesn’t exist or has been moved.
        </p>
        <Link to="/" className="btn-primary mt-5 inline-flex">
          Back to dashboard
        </Link>
      </div>
    </div>
  );
}
