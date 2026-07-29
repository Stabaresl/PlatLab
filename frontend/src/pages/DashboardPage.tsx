import StudentDashboard from "./StudentDashboard"
import InstructorDashboard from "./InstructorDashboard"
import AdminDashboard from "./AdminDashboard"

export default function DashboardPage() {
  /*
   * TODO: Obtener el rol desde el backend cuando esté disponible.
   *
   * Actualmente el rol se guarda en localStorage al iniciar sesión
   * con un valor fijo (ver LoginPage.tsx y SignUpPage.tsx).
   *
   * Cuando el backend devuelva el rol en el endpoint /api/me,
   * reemplazar esto por:
   *
   *   const user = JSON.parse(localStorage.getItem("user") || "{}")
   *   const role = user.role || "estudiante"
   *
   * El backend debe devolver { user: { id, name, email, role } }
   */
  const role = localStorage.getItem("role") || "estudiante"

  switch (role) {
    case "instructor":
      return <InstructorDashboard />
    case "admin":
      return <AdminDashboard />
    default:
      return <StudentDashboard />
  }
}
