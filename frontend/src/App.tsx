import type { FormEvent } from "react"

function App() {
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    // TODO: conectar con backend
  }

  return (
    <main
      className="min-h-screen flex items-center justify-center"
      style={{ backgroundColor: "var(--bg-canvas)", fontFamily: "'Fira Sans', 'Noto Sans', sans-serif" }}
    >
      {/* Card */}
      <div
        className="w-full max-w-sm flex flex-col items-center gap-6 p-8 rounded-lg"
        style={{
          backgroundColor: "var(--bg-surface)",
          border: "1px solid var(--ui-border-default)",
          boxShadow: "var(--shadow-card)",
        }}
      >
        {/* Icono de candado */}
        <div className="flex items-center justify-center w-14 h-14 rounded-lg" style={{ backgroundColor: "var(--accent-danger)" }}>
          <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        </div>

        {/* Título */}
        <h1 className="text-2xl font-semibold text-center" style={{ color: "var(--text-heading)" }}>
          GAIA
        </h1>

        {/* Form */}
        <form onSubmit={handleSubmit} className="w-full flex flex-col gap-4">
          {/* Email */}
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium" style={{ color: "var(--text-base)" }}>
              Email
            </label>
            <input
              type="email"
              placeholder="name@domain.com"
              required
              className="w-full px-3 py-2.5 rounded text-sm outline-none border transition-colors"
              style={{
                backgroundColor: "var(--bg-canvas)",
                borderColor: "var(--ui-border-default)",
                color: "var(--text-heading)",
                fontFamily: "'Fira Sans', 'Noto Sans', sans-serif",
              }}
              onFocus={(e) => (e.target.style.borderColor = "var(--text-base)")}
              onBlur={(e) => (e.target.style.borderColor = "var(--ui-border-default)")}
            />
          </div>

          {/* Password */}
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium" style={{ color: "var(--text-base)" }}>
              Password
            </label>
            <input
              type="password"
              placeholder="············"
              required
              className="w-full px-3 py-2.5 rounded text-sm outline-none border transition-colors"
              style={{
                backgroundColor: "var(--bg-canvas)",
                borderColor: "var(--ui-border-default)",
                color: "var(--text-heading)",
                fontFamily: "'Fira Sans', 'Noto Sans', sans-serif",
              }}
              onFocus={(e) => (e.target.style.borderColor = "var(--text-base)")}
              onBlur={(e) => (e.target.style.borderColor = "var(--ui-border-default)")}
            />
          </div>

          {/* Sign In */}
          <button
            type="submit"
            className="w-full py-2.5 rounded text-sm font-semibold text-white border-none cursor-pointer transition-opacity hover:opacity-90"
            style={{
              backgroundColor: "var(--accent-danger)",
              fontFamily: "'Fira Code', monospace",
            }}
          >
            Sign In
          </button>
        </form>

        {/* Sign Up link */}
        <p className="text-sm" style={{ color: "var(--text-muted)" }}>
          Don&apos;t have an account?{" "}
          <a
            href="#"
            className="font-semibold no-underline hover:underline"
            style={{ color: "var(--accent-danger)" }}
          >
            Sign Up
          </a>
        </p>
      </div>
    </main>
  )
}

export default App
