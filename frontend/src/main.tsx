import { StrictMode, useEffect } from "react"
import { createRoot } from "react-dom/client"
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom"
import "@fontsource/fira-sans/400.css"
import "@fontsource/fira-sans/500.css"
import "@fontsource/fira-sans/600.css"
import "@fontsource/fira-sans/700.css"
import "@fontsource/fira-code/500.css"
import "./index.css"
import LoginPage from "./pages/LoginPage"
import SignUpPage from "./pages/SignUpPage"
import WelcomePage from "./pages/WelcomePage"
import AboutPage from "./pages/AboutPage"
import DashboardPage from "./pages/DashboardPage"
import OAuthCallbackPage from "./pages/OAuthCallbackPage"

const token = () => localStorage.getItem("token")

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  if (!token()) return <Navigate to="/login" replace />
  return <>{children}</>
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  if (token()) return <Navigate to="/dashboard" replace />
  return <>{children}</>
}

function ScrollToTop() {
  const { pathname } = useLocation()
  useEffect(() => { window.scrollTo(0, 0) }, [pathname])
  return null
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <ScrollToTop />
      <Routes>
        <Route path="/" element={<PublicRoute><WelcomePage /></PublicRoute>} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
        <Route path="/signup" element={<PublicRoute><SignUpPage /></PublicRoute>} />
        <Route path="/oauth/:provider/callback" element={<OAuthCallbackPage />} />
        <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
