import { Link, NavLink, Outlet } from 'react-router-dom'

import { useAuth } from '../auth/context'

function navLinkClass({ isActive }: { isActive: boolean }): string {
  const base = 'rounded-full px-4 py-2 text-sm font-medium transition-colors'
  return isActive
    ? `${base} bg-evergreen text-parchment`
    : `${base} text-muted hover:bg-sand hover:text-ink`
}

export function Layout() {
  const { user, loading, signOut } = useAuth()

  return (
    <div className="flex min-h-screen flex-col">
      <a
        href="#main"
        className="sr-only rounded-md bg-evergreen px-4 py-2 text-parchment focus:not-sr-only focus:absolute focus:top-2 focus:left-2"
      >
        Skip to content
      </a>

      <header className="border-b border-sand bg-parchment/90">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3 px-5 py-4">
          <Link to="/" className="font-serif text-xl tracking-tight">
            Walk with God
          </Link>

          <nav aria-label="Main">
            <ul className="flex flex-wrap items-center gap-1">
              <li>
                <NavLink to="/" end className={navLinkClass}>
                  Home
                </NavLink>
              </li>
              <li>
                <NavLink to="/status" className={navLinkClass}>
                  Status
                </NavLink>
              </li>

              {!loading && user && (
                <>
                  <li>
                    <NavLink to="/account" className={navLinkClass}>
                      Account
                    </NavLink>
                  </li>
                  <li>
                    <button
                      type="button"
                      onClick={() => {
                        void signOut().catch(() => undefined)
                      }}
                      className="rounded-full px-4 py-2 text-sm font-medium text-muted transition-colors hover:bg-sand hover:text-ink"
                    >
                      Sign out
                    </button>
                  </li>
                </>
              )}

              {!loading && !user && (
                <li>
                  <NavLink to="/login" className={navLinkClass}>
                    Sign in
                  </NavLink>
                </li>
              )}
            </ul>
          </nav>
        </div>
      </header>

      <main id="main" className="mx-auto w-full max-w-5xl flex-1 px-5 py-12">
        <Outlet />
      </main>

      <footer className="border-t border-sand">
        <div className="mx-auto max-w-5xl px-5 py-6 text-sm text-muted">
          <p>Walk with God — a Jesus-centered journey through Scripture.</p>
        </div>
      </footer>
    </div>
  )
}
