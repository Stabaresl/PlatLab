# PlatLAB

Gamified lab platform for cybersecurity education. Students progress through hands-on challenges (flags, exams) while instructors create, publish, and manage laboratories.

## Stack

- **Backend:** Django 6.0 + Django REST Framework
- **Auth:** JWT via `djangorestframework-simplejwt` + OAuth2 (Google/GitHub)
- **API docs:** drf-spectacular (OpenAPI 3.0)
- **Database:** PostgreSQL
- **Task queue:** Celery + Celery Beat
- **Cache / token store:** Redis
- **Containerization:** Docker & Docker Compose

## Quick start

```bash
# Clone
git clone https://github.com/<org>/platlab.git
cd platlab

# Virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Dependencies
pip install -r requirements.txt

# Environment variables
cp .env.example .env   # then edit with your values

# Database (requires PostgreSQL running)
python manage.py migrate

# Run
python manage.py runserver
```

## Environment variables

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Django secret key | *(required in prod)* |
| `DEBUG` | `True` / `False` | `True` |
| `DB_NAME` | PostgreSQL database name | `platlab` |
| `DB_USER` | PostgreSQL user | `platlab` |
| `DB_PASSWORD` | PostgreSQL password | *(empty)* |
| `DB_HOST` | PostgreSQL host | `localhost` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | *(empty)* |

## Project structure

```
PlatLab/
├── manage.py
├── config/
│   ├── settings/          # base, dev, prod
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── modules/
    ├── shared/            # Domain base classes, infrastructure
    ├── authentication/    # Register, login, OAuth, JWT
    ├── users/             # Profile, admin CRUD
    ├── laboratories/      # Labs, sections, flags, exams
    ├── assignments/       # Invite, accept, deadlines
    ├── progress/          # Dashboard, flag validation, exams
    ├── reports/           # Student bug reports
    ├── notifications/     # In-app & email notifications
    ├── audit/             # Append-only audit log
    └── lab_environments/  # Reserved (not implemented)
```

## Documentation

Full design docs live in [`Documentación/`](Documentación/):

- [Domain model](Documentación/dominio.md)
- [Backend components](Documentación/backend.md)
- [API reference](Documentación/api.md)
- [Security](Documentación/seguridad.md)
- [Folder structure](Documentación/estructura-carpetas.md)
- [Database schema](Documentación/base-de-datos.md)

## License

Internal — Universidad Nacional de Colombia.
