import { Link } from 'react-router-dom'

const walkSections = [
  'Main Passages',
  'Bible History',
  'Walking with God',
  "God's Connections",
  'Treasure to Keep',
  'Short Walk Prayer',
]

export function HomePage() {
  return (
    <div className="space-y-16">
      <section aria-labelledby="hero-title" className="max-w-2xl">
        <p className="mb-3 text-sm font-semibold tracking-widest text-evergreen uppercase">
          A Jesus-centered journey
        </p>
        <h1
          id="hero-title"
          className="font-serif text-4xl leading-tight sm:text-5xl"
        >
          Walk with God, one passage at a time.
        </h1>
        <p className="mt-5 text-lg leading-relaxed text-muted">
          A guided path through Scripture from Genesis to Revelation — reading,
          reflection, and prayer, held together by who God reveals himself to be
          in Jesus.
        </p>

        <dl className="mt-8 flex flex-wrap gap-x-10 gap-y-4 text-sm">
          <div>
            <dt className="text-muted">Walks</dt>
            <dd className="font-serif text-2xl">387</dd>
          </div>
          <div>
            <dt className="text-muted">Parts</dt>
            <dd className="font-serif text-2xl">15</dd>
          </div>
          <div>
            <dt className="text-muted">Sections per Walk</dt>
            <dd className="font-serif text-2xl">6</dd>
          </div>
        </dl>

        <div className="mt-10 flex flex-wrap items-center gap-4">
          <Link
            to="/status"
            className="rounded-full bg-evergreen px-6 py-3 font-medium text-parchment transition-colors hover:bg-evergreen-dark"
          >
            Check the API status
          </Link>
          <p className="text-sm text-muted">
            Accounts and Walks arrive in the next stages.
          </p>
        </div>
      </section>

      <section aria-labelledby="sections-title">
        <h2 id="sections-title" className="font-serif text-2xl">
          Every Walk holds six sections
        </h2>
        <ul className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {walkSections.map((section, index) => (
            <li
              key={section}
              className="rounded-xl border border-sand bg-white/40 p-5"
            >
              <span className="text-xs font-semibold text-muted">
                {String(index + 1).padStart(2, '0')}
              </span>
              <p className="mt-1 font-serif text-lg">{section}</p>
            </li>
          ))}
        </ul>
      </section>

      <section
        aria-labelledby="scripture-note-title"
        className="rounded-xl border border-sand bg-sand/40 p-6"
      >
        <h2 id="scripture-note-title" className="font-serif text-xl">
          Scripture stays Scripture
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-muted">
          Bible text, historical context, and AI-assisted reflection are kept
          separate and clearly labelled. Explanations never replace the Word of
          God, and the application never claims to speak for him.
        </p>
      </section>
    </div>
  )
}
