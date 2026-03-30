import Link from 'next/link'
import { useRouter } from 'next/router'

const links = [
  { href: '/',             label: 'Home' },
  { href: '/analysis',     label: 'Analysis' },
  { href: '/map',          label: 'Map' },
  { href: '/methodology',  label: 'Methodology' },
]

export default function Navbar() {
  const { pathname } = useRouter()

  return (
    <nav className="sticky top-0 z-50 bg-navy-900/90 backdrop-blur border-b border-navy-700">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 font-semibold text-white">
          <span className="text-amber-400 text-xl">$</span>
          <span className="hidden sm:inline text-sm tracking-wide">
            Restaurant <span className="text-amber-400">&</span> Inflation
          </span>
        </Link>

        {/* Nav links */}
        <div className="flex items-center gap-1">
          {links.map(({ href, label }) => {
            const active = pathname === href
            return (
              <Link
                key={href}
                href={href}
                className={`px-3 py-1.5 rounded-md text-sm transition-colors ${
                  active
                    ? 'bg-amber-500/20 text-amber-400 font-medium'
                    : 'text-slate-400 hover:text-white hover:bg-navy-700'
                }`}
              >
                {label}
              </Link>
            )
          })}
        </div>
      </div>
    </nav>
  )
}
