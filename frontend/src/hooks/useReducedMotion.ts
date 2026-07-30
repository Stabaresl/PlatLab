import { useEffect, useState } from "react"

// Los keyframes CSS ya se neutralizan globalmente vía @media (prefers-reduced-motion)
// en index.css, pero las animaciones dirigidas por JS (canvas rAF, anime.js) no
// escuchan ese media query solas — este hook les permite saltar directo al estado
// final en vez de animar.
export default function useReducedMotion() {
  const [reduced, setReduced] = useState(false)

  useEffect(() => {
    const query = window.matchMedia("(prefers-reduced-motion: reduce)")
    setReduced(query.matches)
    const handler = (e: MediaQueryListEvent) => setReduced(e.matches)
    query.addEventListener("change", handler)
    return () => query.removeEventListener("change", handler)
  }, [])

  return reduced
}
