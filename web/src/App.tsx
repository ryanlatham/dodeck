import React, { useState, useEffect } from 'react'
import { useAuth0 } from '@auth0/auth0-react'

function GlassContainer({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-white/20 bg-white/10 backdrop-blur-md shadow-xl p-4">
      {children}
    </div>
  )
}

export default function App() {
  const { loginWithRedirect, logout, isAuthenticated, getAccessTokenSilently, user } = useAuth0()
  const [decks, setDecks] = useState<any[]>([])
  const [search, setSearch] = useState("")
  const apiBase = import.meta.env.VITE_API_BASE_URL

  useEffect(() => {
    const run = async () => {
      if (!isAuthenticated) return
      const token = await getAccessTokenSilently()
      const url = new URL(`${apiBase}/v1/decks`)
      if (search) url.searchParams.set('search', search)
      const res = await fetch(url.toString(), { headers: { Authorization: `Bearer ${token}` } })
      if (res.ok) setDecks((await res.json()).items ?? [])
    }
    run()
  }, [isAuthenticated, search])

  if (!isAuthenticated) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 to-slate-800">
        <GlassContainer>
          <div className="text-white/90 space-y-4">
            <h1 className="text-3xl font-semibold">DoDeck</h1>
            <p className="text-white/70">Sign in to manage your Decks and Dos.</p>
            <button className="rounded-xl px-4 py-2 bg-white/20 hover:bg-white/30" onClick={() => loginWithRedirect()}>
              Login / Sign Up
            </button>
          </div>
        </GlassContainer>
      </main>
    )
  }

  return (
    <main className="min-h-screen p-6 bg-gradient-to-br from-slate-900 to-slate-800 text-white/90">
      <div className="max-w-6xl mx-auto grid md:grid-cols-[280px_1fr] gap-6">
        {/* Left: Decks */}
        <GlassContainer>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold">Decks</h2>
              <button className="rounded-lg px-3 py-1 bg-white/20 hover:bg-white/30">+ New</button>
            </div>
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search..."
              className="w-full rounded-lg bg-white/10 border border-white/20 px-3 py-2 outline-none placeholder-white/50"
            />
            <ul className="space-y-1">
              {decks.map((d, i) => (
                <li key={i} className="rounded-lg px-3 py-2 hover:bg-white/10 cursor-pointer">
                  {d.name || "Example Deck"}
                </li>
              ))}
              {!decks.length && <li className="text-white/50">No decks yet.</li>}
            </ul>
          </div>
        </GlassContainer>

        {/* Right: Dos placeholder */}
        <GlassContainer>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-xl font-semibold">Dos</h2>
            <button className="rounded-lg px-3 py-1 bg-white/20 hover:bg-white/30">+ Add Do</button>
          </div>
          <ul className="space-y-2">
            <li className="rounded-lg px-3 py-2 bg-white/5 border border-white/10 line-through text-white/60">
              Example completed Do
            </li>
            <li className="rounded-lg px-3 py-2 bg-white/5 border border-white/10">
              Example active Do
            </li>
          </ul>
          <div className="mt-6 text-right">
            <button className="rounded-lg px-3 py-1 bg-white/20 hover:bg-white/30"
              onClick={() => logout({ logoutParams: { returnTo: window.location.origin } })}>
              Logout
            </button>
          </div>
        </GlassContainer>
      </div>
      <div className="mt-6 text-white/60 text-sm text-center">Hello {user?.email}</div>
    </main>
  )
}
