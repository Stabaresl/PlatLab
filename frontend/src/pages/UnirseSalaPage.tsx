import { Link, useParams } from "react-router-dom"
import Navbar from "../components/Navbar"
import FondoAscii from "../components/FondoAscii"
import Footer from "../components/Footer"
import { UnirsePanel } from "./SalasPage"

// /salas/unirse/:codigo — destino del enlace de invitación. Si no hay sesión,
// ProtectedRoute manda al login y vuelve aquí después.
export default function UnirseSalaPage() {
  const { codigo = "" } = useParams<{ codigo: string }>()
  const rol = localStorage.getItem("role")
  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: "var(--canvas)", color: "var(--text-base)" }}>
      <FondoAscii />
      <div className="relative z-10 flex flex-col flex-1">
      <Navbar />
      <main className="flex-1">
        <div className="mx-auto px-4 sm:px-6 md:px-8 py-10 flex flex-col gap-6" style={{ maxWidth: "900px" }}>
          <header>
            <h1 className="text-2xl sm:text-3xl font-black uppercase m-0" style={{ color: "var(--text-heading)", fontFamily: "var(--font-display)" }}>
              Entrar a una sala
            </h1>
            <p className="text-sm mt-2 mb-0" style={{ color: "var(--text-muted)" }}>
              Revisa de qué sala se trata y entra: recibirás el laboratorio con tu propio entorno de práctica.
            </p>
          </header>
          {rol && rol !== "estudiante" ? (
            <div className="chamfer p-5 flex flex-col gap-3 items-start" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}>
              <p className="text-sm m-0">Las salas son para estudiantes. Como {rol} puedes crear las tuyas y seguirlas desde su tablero.</p>
              <Link to="/salas" className="consola-btn no-underline">Ir a mis salas →</Link>
            </div>
          ) : (
            <UnirsePanel codigoInicial={codigo} />
          )}
        </div>
      </main>
      <Footer />
      </div>
    </div>
  )
}
