import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import "@fontsource/noto-sans/400.css"
import "@fontsource/noto-sans/500.css"
import "@fontsource/noto-sans/600.css"
import "@fontsource/noto-sans/700.css"
import "@fontsource/fira-code/500.css"
import "./index.css"
import LoginPage from "./pages/LoginPage"
import SignUpPage from "./pages/SignUpPage"
import WelcomePage from "./pages/WelcomePage"

const token = () => localStorage.getItem("token")

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  if (!token()) return <Navigate to="/login" replace />
  return <>{children}</>
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  if (token()) return <Navigate to="/welcome" replace />
  return <>{children}</>
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
        <Route path="/signup" element={<PublicRoute><SignUpPage /></PublicRoute>} />
        <Route path="/welcome" element={<ProtectedRoute><WelcomePage /></ProtectedRoute>} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
