# Estructura de Carpetas — Backend PlatLAB

> Detalle real por módulo (no genérico). Cada módulo replica el mismo patrón de 4 capas + tests, pero con sus propios archivos según sus Casos de Uso, Entidades y Servicios ya aprobados.

```
platlab/
├── manage.py
├── pyproject.toml                 # o requirements/{base,dev,prod}.txt
├── .env.example
├── docker-compose.yml             # provisto/ajustado por el servidor de pregrado
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── prod.py
│   ├── urls.py                    # incluye las urls.py de cada módulo bajo /api/v1/
│   ├── celery.py                  # configuración de Celery + Celery Beat
│   ├── asgi.py
│   └── wsgi.py
│
└── modules/
    ├── shared/
    │   ├── domain/
    │   │   ├── base_entity.py
    │   │   ├── base_value_object.py
    │   │   ├── domain_event.py
    │   │   └── exceptions.py              # BusinessRuleViolationError, NotFoundError, ConflictError
    │   ├── application/
    │   │   └── base_use_case.py            # Template Method
    │   ├── infrastructure/
    │   │   ├── event_dispatcher.py
    │   │   ├── unit_of_work.py             # BaseUnitOfWork
    │   │   ├── redis_client.py
    │   │   ├── email_client.py
    │   │   └── storage_client.py
    │   └── tests/
    │
    ├── authentication/
    │   ├── domain/
    │   │   ├── services.py                 # VinculadorDeCuenta
    │   │   └── exceptions.py               # InvalidCredentialsError, TokenReuseDetectedError, AccountLinkingRequiresConfirmationError
    │   ├── application/
    │   │   ├── dtos.py                     # RegistroDTO, LoginDTO, TokenPairDTO, OAuthProfileDTO
    │   │   └── use_cases/
    │   │       ├── registrar_usuario.py
    │   │       ├── login.py
    │   │       ├── oauth_login.py
    │   │       ├── refresh_token.py
    │   │       ├── logout.py
    │   │       ├── logout_all.py
    │   │       ├── solicitar_recuperacion.py
    │   │       ├── confirmar_recuperacion.py
    │   │       └── verificar_email.py
    │   ├── infrastructure/
    │   │   ├── jwt_service.py               # wrapper sobre SimpleJWT
    │   │   ├── oauth_adapters.py            # GoogleOAuthAdapter, GitHubOAuthAdapter (Adapter)
    │   │   ├── refresh_token_store.py        # backed por Redis
    │   │   └── email_sender.py
    │   ├── presentation/
    │   │   ├── views.py
    │   │   ├── serializers.py
    │   │   └── urls.py
    │   └── tests/
    │       ├── domain/
    │       ├── application/
    │       └── presentation/
    │
    ├── users/
    │   ├── domain/
    │   │   ├── entities.py                 # User, ProveedorAutenticacion
    │   │   ├── value_objects.py             # Rol, Email
    │   │   ├── exceptions.py                # SelfDisableNotAllowedError
    │   │   └── repositories.py              # IUserRepository, IProveedorAutenticacionRepository
    │   ├── application/
    │   │   ├── dtos.py
    │   │   ├── use_cases/
    │   │   │   ├── actualizar_perfil.py
    │   │   │   ├── actualizar_usuario.py
    │   │   │   ├── deshabilitar_usuario.py
    │   │   │   └── habilitar_usuario.py
    │   │   └── queries/
    │   │       ├── obtener_perfil.py
    │   │       ├── listar_usuarios.py
    │   │       ├── obtener_usuario.py
    │   │       └── obtener_usuario_por_email.py   # consumido por Authentication vía Application
    │   ├── infrastructure/
    │   │   ├── models.py
    │   │   ├── repositories.py
    │   │   ├── mappers.py                   # Model ORM ↔ Entidad
    │   │   └── unit_of_work.py
    │   ├── presentation/
    │   │   ├── views.py                     # MeView, UserViewSet
    │   │   ├── serializers.py
    │   │   ├── permissions.py               # IsAdmin, IsSelfOrAdmin
    │   │   └── urls.py
    │   └── tests/
    │
    ├── laboratories/
    │   ├── domain/
    │   │   ├── entities.py                  # Laboratorio, Sección, Examen, Pregunta
    │   │   ├── value_objects.py             # Flag, AyudaProgresiva, Tema, NivelDificultad, EstadoLaboratorio, TipoLaboratorio
    │   │   ├── events.py                    # LaboratoryPublished, LaboratoryDuplicated
    │   │   ├── services.py                  # DuplicadorDeLaboratorio
    │   │   ├── exceptions.py                # CannotEditPredeterminadoError, PublishValidationError
    │   │   └── repositories.py              # ILaboratorioRepository
    │   ├── application/
    │   │   ├── dtos.py
    │   │   ├── use_cases/
    │   │   │   ├── crear_laboratorio.py
    │   │   │   ├── editar_laboratorio.py
    │   │   │   ├── publicar_laboratorio.py
    │   │   │   ├── duplicar_laboratorio.py
    │   │   │   ├── crear_seccion.py
    │   │   │   ├── editar_seccion.py
    │   │   │   ├── definir_flag.py
    │   │   │   ├── crear_examen.py
    │   │   │   └── agregar_pregunta.py
    │   │   └── queries/
    │   │       ├── listar_laboratorios.py
    │   │       ├── obtener_detalle_laboratorio.py
    │   │       └── obtener_toc.py
    │   ├── infrastructure/
    │   │   ├── models.py
    │   │   ├── repositories.py
    │   │   ├── mappers.py
    │   │   ├── content_sanitizer.py          # sanitización HTML del editor WYSIWYG
    │   │   └── unit_of_work.py
    │   ├── presentation/
    │   │   ├── views.py                      # LaboratorioViewSet, SeccionViewSet, FlagView, ExamenViewSet
    │   │   ├── serializers.py
    │   │   ├── permissions.py                # IsInstructorOwner, IsAdminOnlyForPredeterminado
    │   │   └── urls.py
    │   └── tests/
    │
    ├── assignments/
    │   ├── domain/
    │   │   ├── entities.py                  # Asignacion
    │   │   ├── value_objects.py             # EstadoAsignacion, VentanaVencimiento
    │   │   ├── events.py                    # AssignmentInvited, AssignmentAccepted, AssignmentRejected, AssignmentExpired
    │   │   ├── exceptions.py                # DuplicateAssignmentError, InvalidExpirationError
    │   │   └── repositories.py              # IAsignacionRepository
    │   ├── application/
    │   │   ├── dtos.py
    │   │   ├── use_cases/
    │   │   │   ├── invitar_estudiantes.py
    │   │   │   ├── aceptar_invitacion.py
    │   │   │   ├── rechazar_invitacion.py
    │   │   │   └── modificar_vencimiento.py
    │   │   └── queries/
    │   │       ├── listar_asignaciones.py
    │   │       └── filtrar_estudiantes.py
    │   ├── infrastructure/
    │   │   ├── models.py
    │   │   ├── repositories.py
    │   │   ├── mappers.py
    │   │   └── unit_of_work.py
    │   ├── presentation/
    │   │   ├── views.py                      # InvitationViewSet, AssignmentViewSet
    │   │   ├── serializers.py
    │   │   ├── permissions.py
    │   │   └── urls.py
    │   └── tests/
    │
    ├── progress/
    │   ├── domain/
    │   │   ├── entities.py                  # Progreso, ProgresoSeccion, IntentoFlag, ResultadoExamen, HistorialCompletitud
    │   │   ├── value_objects.py             # ContadorFallos, Puntaje
    │   │   ├── events.py                    # FlagValidated, SectionCompleted, PracticeCompleted, ExamGraded
    │   │   ├── services.py                  # ValidadorDeFlag, GestorDeSecuencia, CalificadorDeExamen
    │   │   ├── exceptions.py                # SectionLockedError, ExamNotEligibleError
    │   │   └── repositories.py              # IProgresoRepository
    │   ├── application/
    │   │   ├── dtos.py
    │   │   ├── use_cases/
    │   │   │   ├── validar_flag.py
    │   │   │   └── enviar_examen.py
    │   │   └── queries/
    │   │       ├── obtener_dashboard.py
    │   │       ├── obtener_detalle_progreso.py
    │   │       ├── obtener_contenido_seccion.py
    │   │       ├── obtener_pista.py
    │   │       └── obtener_historial.py
    │   ├── infrastructure/
    │   │   ├── models.py
    │   │   ├── repositories.py
    │   │   ├── mappers.py
    │   │   └── unit_of_work.py
    │   ├── presentation/
    │   │   ├── views.py
    │   │   ├── serializers.py
    │   │   ├── permissions.py                # IsAssignmentOwner
    │   │   └── urls.py
    │   └── tests/
    │
    ├── reports/
    │   ├── domain/
    │   │   ├── entities.py                  # Reporte, AdjuntoReporte
    │   │   ├── value_objects.py             # EstadoReporte
    │   │   ├── events.py                    # ReportSubmitted, ReportResolved
    │   │   ├── exceptions.py                # DescriptionTooShortError
    │   │   └── repositories.py              # IReporteRepository
    │   ├── application/
    │   │   ├── dtos.py
    │   │   ├── use_cases/
    │   │   │   ├── crear_reporte.py
    │   │   │   └── cambiar_estado_reporte.py
    │   │   └── queries/
    │   │       ├── listar_reportes_propios.py
    │   │       └── listar_reportes.py
    │   ├── infrastructure/
    │   │   ├── models.py
    │   │   ├── repositories.py
    │   │   ├── storage_adapter.py            # adjuntos, valida MIME real
    │   │   └── unit_of_work.py
    │   ├── presentation/
    │   │   ├── views.py                      # ReportViewSet
    │   │   ├── serializers.py
    │   │   ├── permissions.py
    │   │   └── urls.py
    │   └── tests/
    │
    ├── notifications/
    │   ├── domain/
    │   │   ├── entities.py                  # Notificacion
    │   │   ├── value_objects.py
    │   │   └── repositories.py              # INotificacionRepository
    │   ├── application/
    │   │   ├── dtos.py
    │   │   ├── use_cases/
    │   │   │   ├── marcar_leida.py
    │   │   │   └── despachar_notificacion.py   # sin endpoint, invocado por listeners
    │   │   └── queries/
    │   │       └── listar_notificaciones.py
    │   ├── infrastructure/
    │   │   ├── models.py
    │   │   ├── repositories.py
    │   │   ├── event_listeners.py            # suscribe AssignmentInvited, AssignmentExpired, PracticeCompleted, ReportResolved
    │   │   ├── email_channel.py
    │   │   ├── in_app_channel.py
    │   │   └── celery_tasks.py               # envío asíncrono
    │   ├── presentation/
    │   │   ├── views.py                      # NotificationViewSet
    │   │   ├── serializers.py
    │   │   └── urls.py
    │   └── tests/
    │
    ├── audit/
    │   ├── domain/
    │   │   ├── entities.py                  # RegistroAuditoria
    │   │   ├── exceptions.py
    │   │   └── repositories.py              # IAuditoriaRepository (solo save/find)
    │   ├── application/
    │   │   ├── dtos.py
    │   │   ├── use_cases/
    │   │   │   └── registrar_auditoria.py    # sin endpoint, invocado por listeners
    │   │   └── queries/
    │   │       └── consultar_auditoria.py
    │   ├── infrastructure/
    │   │   ├── models.py
    │   │   ├── repositories.py
    │   │   └── event_listeners.py            # suscribe TODOS los eventos de dominio
    │   ├── presentation/
    │   │   ├── views.py                      # AuditViewSet (solo lectura)
    │   │   ├── serializers.py
    │   │   ├── permissions.py                # IsAdmin
    │   │   └── urls.py
    │   └── tests/
    │
    └── lab_environments/                    # RESERVADO — sin implementación
        ├── domain/
        │   └── repositories.py               # IEntornoRepository (interfaz stub, sin entidades aún)
        └── README.md                         # explica que se activa cuando existan HU de entornos en vivo
```

## Estado
✅ Estructura real por módulo, sin genéricos. Cada archivo listado corresponde a un componente ya nombrado en `backend.md`, `dominio.md` o `arquitectura.md` — ninguno es inventado en este documento.
