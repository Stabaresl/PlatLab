// Set mínimo de iconos inline (outline, stroke=currentColor) reutilizados
// en encabezados de sección de los dashboards — evita duplicar <svg> sueltos.
import type { SVGProps } from "react"

function Base(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      width={18}
      height={18}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={1.75}
      {...props}
    />
  )
}

export const IconChart = (props: SVGProps<SVGSVGElement>) => (
  <Base {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M3 3v18h18M7 15l4-6 4 3 5-8" /></Base>
)
export const IconUsers = (props: SVGProps<SVGSVGElement>) => (
  <Base {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" /></Base>
)
export const IconFlask = (props: SVGProps<SVGSVGElement>) => (
  <Base {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3v6.75L4.5 19.5A1.5 1.5 0 005.85 21.75h12.3a1.5 1.5 0 001.35-2.25L14.25 9.75V3M8.25 3h7.5" /></Base>
)
export const IconMail = (props: SVGProps<SVGSVGElement>) => (
  <Base {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></Base>
)
export const IconTrophy = (props: SVGProps<SVGSVGElement>) => (
  <Base {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M8.25 3h7.5v3a3.75 3.75 0 11-7.5 0V3zM6 6H3.75A2.25 2.25 0 016 3.75V6zm12 0h2.25A2.25 2.25 0 0018 3.75V6zM12 12v6m-3 3h6" /></Base>
)
export const IconClock = (props: SVGProps<SVGSVGElement>) => (
  <Base {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 2m6-2a9 9 0 11-18 0 9 9 0 0118 0z" /></Base>
)
export const IconExam = (props: SVGProps<SVGSVGElement>) => (
  <Base {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6M9 8h1m5 13H6a2 2 0 01-2-2V5a2 2 0 012-2h7l5 5v11a2 2 0 01-2 2z" /></Base>
)
export const IconRocket = (props: SVGProps<SVGSVGElement>) => (
  <Base {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M15.59 14.37a6 6 0 01-5.84 7.38v-4.8m5.84-2.58a14.98 14.98 0 006.16-12.12A14.98 14.98 0 009.63 8.72m5.96 5.65a14.98 14.98 0 01-5.96-5.65m0 0a14.98 14.98 0 00-5.16 6.32m5.16-6.32L9.63 8.72M4.47 14.37a6 6 0 004.4 5.84m0 0v-4.8" /></Base>
)
export const IconGauge = (props: SVGProps<SVGSVGElement>) => (
  <Base {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9 9 0 100-18 9 9 0 000 18zm0-4l3-6" /></Base>
)
