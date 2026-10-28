import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from './context'

/** Renders child routes only for signed-in users. */
export function ProtectedRoute() {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return (
      <p className="text-muted" role="status">
        Checking your session…
      </p>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return <Outlet />
}
