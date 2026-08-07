# Cargo

**Fast LAN file transfer for people who would rather not email themselves a 2 GB archive.**

## Overview

Cargo is a local-first file transfer system designed for Local Area Networks. It lets people move files quickly between their own devices on the same network, without relying on cloud storage or a complicated setup.

The problem Cargo solves is simple: moving a file from one machine to another should not feel like a small software project. On a LAN, speed matters, privacy matters, and setup should be close to zero. Cargo makes that possible with a short transfer code, a QR code, and a lightweight web interface.

Cargo is a good fit for offices, classrooms, homes, labs, and any environment where devices already share a network and the only thing missing is a practical way to share files.

## Features

- Fast file transfers over LAN.
- Web-based upload and download flows.
- Short transfer codes for quick handoff between devices.
- QR code output for easy scanning on a second device.
- Secure authentication with JWT-based access tokens.
- Multi-user support.
- Disk-based file storage with PostgreSQL metadata.
- Background cleanup jobs for expired transfers.
- Search and folder organization for uploaded files.
- REST API first, with a polished browser interface built on top.
- Docker Compose-based deployment for local self-hosting.

## Tech Stack

- Python 3.13
- FastAPI
- SQLAlchemy 2.0
- PostgreSQL
- Redis
- Celery
- Alembic
- Docker and Docker Compose
- Pydantic v2
- Pytest

## Architecture

Cargo follows a clean, layered structure:

- **API**: FastAPI routes expose the REST API and serve the browser UI.
- **Database**: PostgreSQL stores metadata only, including users, folders, and transfer records.
- **Redis**: Used for background queues, caching, sessions, progress, and simple coordination.
- **Celery workers**: Run background cleanup tasks and other async jobs that should not block the request path.
- **Docker**: Packages the application, database, Redis, and workers so the full system starts with one command.

## Getting Started

### Prerequisites

- Docker
- Docker Compose

### 1. Clone the repository

```bash
git clone <repository-url>
cd Cargo
```

### 2. Configure environment variables

Cargo reads configuration from `CARGO_*` environment variables. The Docker Compose file already includes working defaults for local development, but you can adjust them if needed:

- `CARGO_DATABASE_URL`
- `CARGO_REDIS_URL`
- `CARGO_DATA_DIR`
- `CARGO_UPLOADS_DIR`
- `CARGO_TEMP_DIR`
- `CARGO_TRANSFER_CODE_TTL_SECONDS`
- `CARGO_CLEANUP_INTERVAL_SECONDS`

### 3. Start the stack

```bash
docker compose up --build
```

### 4. Open the application

- Web UI: `http://localhost:8000`
- Upload page: `http://localhost:8000/upload`
- Download page: `http://localhost:8000/download`
- API base: `http://localhost:8000/api/v1`

## Project Structure

```text
Cargo/
├── app/
│   ├── api/
│   │   ├── dependencies.py
│   │   ├── router.py
│   │   ├── routes/
│   │   └── schemas/
│   ├── application/
│   ├── core/
│   ├── domain/
│   ├── infrastructure/
│   ├── main.py
│   └── static/
├── migrations/
├── tests/
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
└── requirements.txt
```

## Development

### Run locally

If you want to run the application outside Docker, install the dependencies and start Uvicorn against the FastAPI app:

```bash
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Apply migrations

Cargo uses Alembic for database migrations.

```bash
alembic upgrade head
```

### Useful Docker commands

```bash
docker compose up --build
docker compose down
docker compose logs -f api
docker compose logs -f worker
```

## Roadmap

The current MVP focuses on the core LAN transfer flow. Planned improvements include:

- Resume interrupted transfers.
- Web interface refinements and transfer history.
- More granular authentication and permissions.
- Stronger transfer integrity verification across all file paths.
- Additional transfer management features for active users.

## Contributing

Contributions are welcome.

If you want to help, the best starting point is to open an issue or discussion describing the problem or improvement you want to make. Please keep changes focused, follow the existing architecture, and include tests when practical.

## License

MIT LICENSING.
