import StudentDashboard from "./StudentDashboard"
import InstructorDashboard from "./InstructorDashboard"
import AdminDashboard from "./AdminDashboard"

export default function DashboardPage() {
  // El rol real (`estudiante` | `instructor` | `administrador`, VO `Rol` del
  // backend) viene del claim `rol` del JWT y se guarda en localStorage al
  // iniciar sesión (ver LoginPage/SignUpPage/OAuthCallbackPage).
  const role = localStorage.getItem("role") || "estudiante"

  switch (role) {
    case "instructor":
      return <InstructorDashboard />
    case "administrador":
      return <AdminDashboard />
    default:
      return <StudentDashboard />
  }
}
