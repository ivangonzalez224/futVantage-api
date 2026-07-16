# FutVantage API (Backend)

API backend para FutVantage: plataforma de análisis táctico de fútbol para categorías juveniles y academias de fútbol base. Este repositorio contiene la API REST y la capa de procesamiento analítico (heatmaps, redes de pase, radares de rendimiento).

> El frontend (interfaz de anotación + dashboards) vive en un repositorio separado: `tactical-scout-web`.

## Stack

- **Python 3.12** + **FastAPI**
- **Pydantic v2** / **pydantic-settings** para validación y configuración
- **PostgreSQL** (próxima feature: capa de base de datos con SQLAlchemy)
- **pytest** + **pytest-cov** para tests
- **Ruff** para lint y formato (reemplaza flake8 + black + isort en una sola herramienta, mucho más rápida)
- **mypy** en modo estricto para chequeo de tipos
- **pre-commit** para hooks de Git (equivalente a Husky en el frontend)
- **GitHub Actions** para CI — sin Docker

## Requisitos

- Python 3.11+
- pip

## Setup local

\`\`\`bash
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -e ".[dev]"
.venv/bin/pre-commit install
cp .env.example .env
\`\`\`

En adelante, activa el entorno virtual en cada sesión de terminal:
\`\`\`bash
source .venv/bin/activate
\`\`\`

## Correr el servidor

\`\`\`bash
uvicorn app.main:app --reload
\`\`\`

Abre [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health) — deberías ver `{"status": "ok"}`.

Documentación interactiva autogenerada por FastAPI: [http://localhost:8000/docs](http://localhost:8000/docs).

## Comandos disponibles

| Comando | Descripción |
|---|---|
| `uvicorn app.main:app --reload` | Levanta el servidor de desarrollo con recarga automática |
| `ruff check .` | Corre el linter |
| `ruff check --fix .` | Corre el linter y corrige lo posible |
| `ruff format .` | Formatea el código |
| `ruff format --check .` | Verifica formato sin modificar archivos |
| `mypy app tests` | Chequeo de tipos estricto |
| `pytest` | Corre la suite de tests |
| `pytest --cov=app --cov-report=term-missing` | Corre tests con reporte de cobertura |

## Estructura del proyecto

\`\`\`
app/
  main.py           # Entry point, application factory
  core/
    config.py       # Configuración vía variables de entorno
  api/
    routes/         # Endpoints agrupados por recurso
tests/               # Tests, misma estructura que app/
\`\`\`

## Convenciones

- **Commits**: [Conventional Commits](https://www.conventionalcommits.org/) en inglés (`feat:`, `fix:`, `chore:`, `test:`, `ci:`, `docs:`, `refactor:`).
- **Pre-commit**: corre Ruff (lint + format) y mypy automáticamente antes de cada commit.
- **Tipado estricto**: todo el código en `app/` debe pasar `mypy --strict`.
- **CI**: todo PR contra `main` corre lint, format check, type check y tests con cobertura en GitHub Actions.
- **Sin Docker**: el proyecto corre directo con un entorno virtual de Python, sin contenedores.

## Roadmap (Fase 1 — MVP)

- [x] Scaffolding del proyecto (FastAPI, Ruff, mypy, pytest, pre-commit, CI)
- [ ] Capa de base de datos (SQLAlchemy + PostgreSQL) siguiendo el esquema de `events`, `players`, `matches`, `teams`
- [ ] Endpoints CRUD de eventos (`POST /matches/{id}/events`, etc.)
- [ ] Validaciones de negocio (destino obligatorio según tipo, body_part obligatorio en remates, etc.)
- [ ] Endpoints de reportes (mapa de acciones, radar de jugador)