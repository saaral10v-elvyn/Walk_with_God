import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <div className="max-w-xl">
      <p className="text-sm font-semibold tracking-widest text-evergreen uppercase">
        404
      </p>
      <h1 className="mt-2 font-serif text-3xl">This path does not exist</h1>
      <p className="mt-3 text-muted">
        The page you were looking for has not been built yet, or the address is
        incorrect.
      </p>
      <Link
        to="/"
        className="mt-8 inline-block rounded-full bg-evergreen px-6 py-3 font-medium text-parchment transition-colors hover:bg-evergreen-dark"
      >
        Return home
      </Link>
    </div>
  )
}
