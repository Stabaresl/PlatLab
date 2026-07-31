import { StrictMode, useEffect } from "react"
import { createRoot } from "react-dom/client"
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom"
import "@fontsource/fira-sans/400.css"
import "@fontsource/fira-sans/500.css"
import "@fontsource/fira-sans/600.css"
import "@fontsource/fira-sans/700.css"
import "@fontsource/fira-code/500.css"
import "@fontsource/orbitron/500.css"
import "@fontsource/orbitron/700.css"
import "@fontsource/orbitron/900.css"
import "@fontsource/jetbrains-mono/400.css"
import "@fontsource/jetbrains-mono/500.css"
import "@fontsource/jetbrains-mono/700.css"
import "./index.css"
import LoginPage from "./pages/LoginPage"
import SignUpPage from "./pages/SignUpPage"
import WelcomePage from "./pages/WelcomePage"
import AboutPage from "./pages/AboutPage"
import DashboardPage from "./pages/DashboardPage"
import OAuthCallbackPage from "./pages/OAuthCallbackPage"
import CatalogPage from "./pages/CatalogPage"
import LabDetailPage from "./pages/LabDetailPage"
import ResolverLaboratorioPage from "./pages/ResolverLaboratorioPage"
import SeccionMaterialPage from "./pages/SeccionMaterialPage"
import CrearLaboratorioPage from "./pages/CrearLaboratorioPage"
import LabPreviewPage from "./pages/LabPreviewPage"

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
        {/* Sin PublicRoute a propósito: el logo/GA::IA del Navbar siempre
            vuelve acá, incluso con sesión iniciada — antes redirigía a
            /dashboard y el usuario nunca podía volver a ver la landing. */}
        <Route path="/" element={<WelcomePage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="/laboratorios" element={<CatalogPage />} />
        <Route path="/laboratorios/:id" element={<LabDetailPage />} />
        <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
        <Route path="/signup" element={<PublicRoute><SignUpPage /></PublicRoute>} />
        <Route path="/oauth/:provider/callback" element={<OAuthCallbackPage />} />
        <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
        <Route path="/resolver/:assignmentId" element={<ProtectedRoute><ResolverLaboratorioPage /></ProtectedRoute>} />
        <Route path="/resolver/:assignmentId/secciones/:seccionId/material" element={<ProtectedRoute><SeccionMaterialPage /></ProtectedRoute>} />
        <Route path="/laboratorios/nuevo" element={<ProtectedRoute><CrearLaboratorioPage /></ProtectedRoute>} />
        <Route path="/laboratorios/:id/revision" element={<ProtectedRoute><LabPreviewPage /></ProtectedRoute>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
