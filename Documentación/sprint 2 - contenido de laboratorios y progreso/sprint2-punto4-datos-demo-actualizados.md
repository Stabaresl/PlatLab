# Sprint 2 — Punto 4: `seed_demo_data` actualizado al flujo real

## ¿Qué es esto?

Reescritura del management command `seed_demo_data` para que reproduzca el
**flujo real de la plataforma** de punta a punta, en vez de crear un
laboratorio suelto ya asignado directamente — que es como funcionaba antes,
pero no como funciona la plataforma en producción.

## ¿Por qué es importante?

El comando existe para poder probar el frontend sin cargar nada a mano. Si
los datos que genera no respetan el flujo real (plantilla → duplicado del
instructor → invitación → aceptación), no sirve para detectar bugs de ese
flujo ni da una demo representativa. Además, con la guía práctica y las
reglas de vencimiento/examen del resto de este sprint, hacía falta que el
laboratorio semilla tuviera contenido real para poder probarlas manualmente.

## ¿Qué se hizo exactamente?

El comando ahora, en orden, con los tres usuarios de siempre (uno por rol):

1. **El admin crea un laboratorio `predeterminado`** (plantilla), con
   secciones — incluyendo la guía práctica (`EntornoPractica`) del punto 1
   de este sprint — y una flag definida, y lo **publica**. Al ser
   `predeterminado` y estar publicado, aparece en el catálogo público
   (`/laboratorios`, HV-02) para cualquier visitante, sin necesidad de
   invitación.
2. **El instructor lo duplica** (`DuplicarLaboratorioUseCase`, UC-05) — el
   mismo camino que seguiría un instructor real desde "Ver detalle" en el
   catálogo — y obtiene su propia copia `personalizado`. La duplicación
   copia secciones y flags pero **no** el examen (a propósito: el
   instructor siempre debe revisar/recrear el examen de su copia). El
   comando publica esa copia y le agrega el examen.
3. **El instructor invita al estudiante a su copia** (no a la plantilla —
   un laboratorio `predeterminado` no se puede asignar directamente,
   `dominio.md §4`), y la invitación se acepta en el mismo comando,
   inicializando el `Progreso` correspondiente.

Resultado: la plantilla queda visible en el catálogo para cualquiera, y el
estudiante ve **su copia asignada** ya lista en su Dashboard, con progreso
en cero, examen configurado, y ventana de vencimiento activa.

### Bug que este cambio expuso y corrigió de paso

Antes de este cambio, un laboratorio `personalizado` ya asignado a un
estudiante **no aparecía en el catálogo público** — comportamiento correcto
por diseño, es privado del instructor — pero **tampoco se podía ver su
detalle/TOC desde el Dashboard del estudiante**, por un bug de visibilidad
en `ObtenerDetalleLaboratorioQuery` que hasta ahora nadie había ejercitado
porque el seed anterior no reproducía ese camino. Se corrigió como parte de
este mismo trabajo.

### Idempotencia
El comando es idempotente: correrlo de nuevo no duplica usuarios, la
plantilla ni la copia del instructor (busca por email/relación existente
antes de crear). Si un paso anterior no llegó a completarse (por ejemplo,
se cortó a mitad de camino), sí reintenta los pasos que falten.

## Credenciales que deja creadas

| Rol | Email | Contraseña |
|---|---|---|
| Administrador | `admin@platlab.demo` | `Admin1234` |
| Instructor | `instructor@platlab.demo` | `Instructor1234` |
| Estudiante | `estudiante@platlab.demo` | `Estudiante1234` |

Uso: `docker compose exec web python manage.py seed_demo_data` (detalle de
instalación completo en el `README.md` de la raíz del repo).

## En una frase

El comando de datos demo dejó de crear un laboratorio "de juguete" ya
armado a mano, y pasó a ejercitar el flujo real completo (plantilla
pública → duplicado del instructor → invitación aceptada), lo cual de paso
destapó y permitió corregir un bug real de visibilidad que el seed anterior
nunca llegaba a tocar.
