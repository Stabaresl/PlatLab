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
export const IconSearch = (props: SVGProps<SVGSVGElement>) => (
  <Base {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35M18 10.5a7.5 7.5 0 11-15 0 7.5 7.5 0 0115 0z" /></Base>
)
export const IconArrowRight = (props: SVGProps<SVGSVGElement>) => (
  <Base {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3" /></Base>
)
export const IconLock = (props: SVGProps<SVGSVGElement>) => (
  <Base {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-12v3H8V7a4 4 0 118 0z" /></Base>
)
export const IconBell = (props: SVGProps<SVGSVGElement>) => (
  <Base {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M18 8a6 6 0 10-12 0c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 01-3.46 0" /></Base>
)
export const IconActivity = (props: SVGProps<SVGSVGElement>) => (
  <Base {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M22 12h-4l-3 9L9 3l-3 9H2" /></Base>
)
export const IconGlobe = (props: SVGProps<SVGSVGElement>) => (
  <Base {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9 9 0 100-18 9 9 0 000 18zM3.6 9h16.8M3.6 15h16.8M12 3a14.5 14.5 0 010 18M12 3a14.5 14.5 0 000 18" /></Base>
)
export const IconGlasses = (props: SVGProps<SVGSVGElement>) => (
  <Base {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M4 15a3 3 0 106 0 3 3 0 00-6 0zm10 0a3 3 0 106 0 3 3 0 00-6 0zM10 15h4M2 9l2 6M22 9l-2 6M8 9h8" /></Base>
)
export const IconMask = (props: SVGProps<SVGSVGElement>) => (
  <Base {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M3 10c0-3 4-5 9-5s9 2 9 5-4 8-9 8-9-5-9-8zM8 11l1.5 1.5M16 11l-1.5 1.5M9 15c1 1 5 1 6 0" /></Base>
)
export const IconBackpack = (props: SVGProps<SVGSVGElement>) => (
  <Base {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M7 8V6a5 5 0 0110 0v2M5 10a2 2 0 012-2h10a2 2 0 012 2v9a2 2 0 01-2 2H7a2 2 0 01-2-2v-9zM9 10v3h6v-3M9 20v-4h6v4" /></Base>
)

// ── Piezas del avatar (una por TipoCosmetico) ──
export const IconHoodie = (props: SVGProps<SVGSVGElement>) => (
  <Base {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M8 4l4 3 4-3 4 3v4l-3 1v8H7v-8l-3-1V7l4-3zM10 7v3a2 2 0 004 0V7" /></Base>
)
export const IconAura = (props: SVGProps<SVGSVGElement>) => (
  <Base {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M12 15a3 3 0 100-6 3 3 0 000 6zM12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9L7 7M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1" /></Base>
)
export const IconInsignia = (props: SVGProps<SVGSVGElement>) => (
  <Base {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M12 3l7 3v5c0 5-3.5 8.5-7 10-3.5-1.5-7-5-7-10V6l7-3zM12 8l1.2 2.4 2.6.4-1.9 1.8.5 2.6L12 14l-2.4 1.2.5-2.6-1.9-1.8 2.6-.4L12 8z" /></Base>
)
export const IconGuantes = (props: SVGProps<SVGSVGElement>) => (
  <Base {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M7 21v-5l-2.5-4.5a1.5 1.5 0 012.6-1.5L8 11.5V5a1.5 1.5 0 013 0v5M11 4a1.5 1.5 0 013 0v6M14 5a1.5 1.5 0 013 0v6M17 8a1.5 1.5 0 013 0v6c0 3-2 7-6 7H7" /></Base>
)
export const IconZapatos = (props: SVGProps<SVGSVGElement>) => (
  <Base {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M3 16v-4l3-1 3 2 4-1 3 2 5 1v3H3zM3 19h18M9 13l1-2M13 12l1-2" /></Base>
)
export const IconGorra = (props: SVGProps<SVGSVGElement>) => (
  <Base {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M5 15a7 7 0 0114 0v1H5v-1zM12 8V6M19 16h3M12 8a7 7 0 00-3 .7" /></Base>
)
export const IconAudifonos = (props: SVGProps<SVGSVGElement>) => (
  <Base {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M4 15v-3a8 8 0 0116 0v3M4 15a2 2 0 012-2h1v6H6a2 2 0 01-2-2v-2zM20 15a2 2 0 00-2-2h-1v6h1a2 2 0 002-2v-2z" /></Base>
)
export const IconMarco = (props: SVGProps<SVGSVGElement>) => (
  <Base {...props}><path strokeLinecap="round" strokeLinejoin="round" d="M7 3h14v14l-4 4H3V7l4-4zM8 8h8v8H8z" /></Base>
)
