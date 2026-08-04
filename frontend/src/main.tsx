import { StrictMode, Suspense, lazy, useEffect } from "react"
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
import OnboardingTour from "./components/OnboardingTour"

// Cada página es su propio chunk (RNF rendimiento — antes un único
// bundle de 1.2MB, todo eager acá). El usuario solo paga por descargar
// la página a la que entra, no las otras 17.
const LoginPage = lazy(() => import("./pages/LoginPage"))
const SignUpPage = lazy(() => import("./pages/SignUpPage"))
const WelcomePage = lazy(() => import("./pages/WelcomePage"))
const AboutPage = lazy(() => import("./pages/AboutPage"))
const DashboardPage = lazy(() => import("./pages/DashboardPage"))
const OAuthCallbackPage = lazy(() => import("./pages/OAuthCallbackPage"))
const CatalogPage = lazy(() => import("./pages/CatalogPage"))
const LabDetailPage = lazy(() => import("./pages/LabDetailPage"))
const ResolverLaboratorioPage = lazy(() => import("./pages/ResolverLaboratorioPage"))
const SeccionMaterialPage = lazy(() => import("./pages/SeccionMaterialPage"))
const CrearLaboratorioPage = lazy(() => import("./pages/CrearLaboratorioPage"))
const LabPreviewPage = lazy(() => import("./pages/LabPreviewPage"))
const RoadmapPage = lazy(() => import("./pages/RoadmapPage"))
const RoadmapAdminPage = lazy(() => import("./pages/RoadmapAdminPage"))
const ProfilePage = lazy(() => import("./pages/ProfilePage"))

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

function PageLoader() {
  return (
    <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: "var(--canvas)" }}>
      <span className="text-xs uppercase tracking-widest" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
        root@platlab:~$ cargando…
      </span>
    </div>
  )
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <ScrollToTop />
      <OnboardingTour />
      <Suspense fallback={<PageLoader />}>
        <Routes>
          {/* Sin PublicRoute a propósito: el logo/PLAT::LAB del Navbar siempre
              vuelve acá, incluso con sesión iniciada — antes redirigía a
              /dashboard y el usuario nunca podía volver a ver la landing. */}
          <Route path="/" element={<WelcomePage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/laboratorios" element={<CatalogPage />} />
          <Route path="/laboratorios/:id" element={<LabDetailPage />} />
          <Route path="/roadmap" element={<RoadmapPage />} />
          <Route path="/roadmap/admin" element={<ProtectedRoute><RoadmapAdminPage /></ProtectedRoute>} />
          <Route path="/profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
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
      </Suspense>
    </BrowserRouter>
  </StrictMode>,
)
