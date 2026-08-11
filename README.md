# Cargo

<img width="1152" height="648" alt="cargo" src="https://github.com/user-attachments/assets/7a519440-9112-44df-b653-366bc83e06af" />

**Fast LAN file transfer for people who would rather not email themselves a 2 GB archive.**

## Overview

Cargo is a local-first file transfer system designed for Local Area Networks. It lets people move files quickly between their own devices on the same network, without relying on cloud storage or a complicated setup.

The problem Cargo solves is simple: moving a file from one machine to another should not feel like a small software project. On a LAN, speed matters, privacy matters, and setup should be close to zero. Cargo makes that possible with a short transfer code, a QR code, and a lightweight web interface.

Cargo is a good fit for offices, classrooms, homes, labs, and any environment where devices already share a network and the only thing missing is a practical way to share files.

## Features

- Fast file transfers over LAN.
- Web-based upload and download flows.
- Compatible with free services, such as Tailscale and Radmin
- Short transfer codes for quick handoff between devices.
- QR code output for easy scanning on a second device.
- Secure authentication with JWT-based access tokens.
- Multi-user support.
- Disk-based file storage with PostgreSQL metadata.
- Background cleanup jobs for expired transfers.
- Search and folder organization for uploaded files.
- REST API first, with a polished browser interface built on top.
- Docker Compose-based deployment for local self-hosting.
- Chunked uploads for reliable large file transfers.

 ## Security

- JWT authentication.
- Expiring transfer codes.
- Metadata separated from file storage.
- No cloud dependency.
- Local network only by default.

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
git clone https:://github.com/LUFFE154/Cargo
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

```text
start.bat
```

The script will:

1. Check that Docker is running.
2. Start the PostgreSQL and Redis containers.
3. Build the application containers.
4. Start the complete Cargo stack.

Or in the console:

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
│
├── migrations/
├── tests/
│
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
├── requirements.txt
│
├── start.bat
├── dev.bat
├── stop.bat
│
├── .env.example
├── .gitignore
└── README.md
```

## Development

### Run locally

If you want to run the application outside Docker, install the dependencies and start Uvicorn against the FastAPI app:

#### 1. Run the development environment

Double-click:

```text
dev.bat
```

The script automatically:

- Checks for Python.
- Creates the `.venv` virtual environment if necessary.
- Activates the virtual environment.
- Installs the dependencies from `requirements.txt`.
- Starts the FastAPI development server.

Or:

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

## Network Access

Cargo is designed to work beyond `localhost`.

The Docker deployment exposes the application through the host machine's network interface, which means Cargo can be accessed using any reachable IP address of the host, provided that the network is correctly configured.

For example, you can use Cargo through:

- Local Area Network (LAN) IP addresses
- Port forwarding
- **Tailscale**
- **Radmin VPN**
- Other VPN or virtual network interfaces
- IPv6 addresses
- Other network configurations capable of routing traffic to the host

### Example

If the machine running Cargo has the LAN address:

```text
192.168.1.100
```

Another device on the same network can access:

```text
http://192.168.1.100:8000
```

Similarly, if the host is reachable through a Tailscale address:

```text
http://100.x.x.x:8000
```

Cargo can be accessed through that address as well.

### Port Forwarding

Cargo can also be exposed through port forwarding when the host is reachable from outside the local network.

For example:

```text
Internet
    |
    v
Router
    |
    | Port 8000
    v
Cargo Host
    |
    v
Docker Container
    |
    v
Cargo
```

The exact configuration depends on the router, firewall, ISP, and network topology.

> **Security note:** Exposing Cargo outside your trusted LAN changes its security requirements. If you expose the application to the public Internet, use appropriate authentication, firewall rules, HTTPS/reverse proxying, and network access controls. Cargo is primarily designed as a local-first file transfer system and should not be assumed to be safe for unrestricted public exposure without additional hardening.

### IPv6

Cargo can also be used over IPv6 when Docker, the host operating system, and the network are configured for IPv6.

For example:

```text
http://[2001:db8::1234]:8000
```

IPv6 addresses must be enclosed in square brackets when specifying a port in a URL.

### Network Requirements

For another device to access Cargo, the following must be true:

1. The Cargo host must be reachable from the client device.
2. Port `8000` must be exposed by Docker.
3. The host firewall must allow the connection.
4. Any router, VPN, or tunnel involved must correctly route the traffic.
5. The Cargo service must be listening on the appropriate host interface.

Cargo itself does not require a specific VPN or networking solution. It works with the network connectivity provided by the host environment.

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

MIT License.

## Author
Luiz Fernando Pio Ferreira
luffe533@gmail.com
