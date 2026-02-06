# Face Recognition System - Docker Deployment Guide

## Overview
This Docker setup allows you to run the Face Recognition System (Frontend + Backend + Database) on your Ubuntu server (192.168.5.74) and access it from any machine on the network.

## Architecture
- **Frontend**: React + Vite app served via Nginx on port 3000
- **Backend**: Spring Boot REST API on port 8080
- **Database**: PostgreSQL database on port 5432
- **Network**: All services communicate through a dedicated Docker network

## Prerequisites
- Docker and Docker Compose installed on Ubuntu server (192.168.5.74)
- Ubuntu server has network connectivity
- Ports 3000, 8080, and 5432 are available

## Installation & Startup

### 1. Navigate to the integration directory
```bash
cd /home/javi/dev/University/Semestre11/face_recognition_system/integration
```

### 2. Build and start all services
```bash
docker-compose up -d --build
```

This command will:
- Build the frontend image (React + Nginx)
- Build the backend image (Spring Boot)
- Pull PostgreSQL image
- Start all containers and create the network

### 3. Verify services are running
```bash
docker-compose ps
```

You should see three running containers:
- face_recognition_db (PostgreSQL)
- face_recognition_backend (Spring Boot)
- face_recognition_frontend (Nginx)

## Access from Another Computer

Once running, access the system from any computer on the network using the server's IP address (192.168.5.74):

- **Frontend**: http://192.168.5.74:3000
- **Backend API**: http://192.168.5.74:8080/api
- **Database** (if needed): postgresql://192.168.5.74:5432/security_db
  - Username: postgres
  - Password: postgres

## Useful Commands

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
```

### Stop all services
```bash
docker-compose down
```

### Stop and remove all data (including database)
```bash
docker-compose down -v
```

### Rebuild and restart (useful after code changes)
```bash
docker-compose up -d --build
```

### Enter a running container shell
```bash
# Backend
docker exec -it face_recognition_backend /bin/sh

# Frontend
docker exec -it face_recognition_frontend /bin/sh

# Database
docker exec -it face_recognition_db psql -U postgres
```

## Port Bindings

All ports are bound to `0.0.0.0:port` to ensure accessibility from other machines:

- `0.0.0.0:3000:3000` - Frontend (Nginx)
- `0.0.0.0:8080:8080` - Backend (Spring Boot)
- `0.0.0.0:5432:5432` - Database (PostgreSQL)

This means services will be accessible from:
- The server itself (localhost)
- Other machines on the network (using server IP: 192.168.5.74)
- External networks (if firewall allows)

## Environment Variables

The docker-compose.yml includes environment variables for:
- **Backend database connection**: Uses container service name `db` for internal DNS resolution
- **Frontend API URL**: Configured to use the `backend` service name for internal Docker network communication
- **PostgreSQL**: Default credentials are configured in compose file

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs db
```

### Database connection errors
- Ensure PostgreSQL is healthy: `docker-compose logs db`
- Wait 30+ seconds after startup for backend to connect
- Backend has a 30-second startup period before health checks

### Frontend can't reach backend
- Check if backend is healthy: `docker-compose ps`
- Verify Nginx configuration proxying
- Check network connectivity: `docker-compose logs frontend`

### Port conflicts
If ports 3000, 8080, or 5432 are already in use:
1. Edit docker-compose.yml
2. Change the first port number in port mappings (e.g., `3001:3000`)
3. Rebuild: `docker-compose up -d --build`

## Performance Notes

- Initial build may take several minutes
- Spring Boot backend takes ~30 seconds to start
- Nginx proxy adds minimal overhead
- Database volume is persistent (data survives container restarts)

## Security Notes

⚠️ **For Development Only**: Current setup uses default passwords and is not production-hardened.

For production deployment:
- Change PostgreSQL passwords in docker-compose.yml
- Remove `0.0.0.0` bindings (use localhost or specific IPs)
- Add CORS configuration to backend
- Enable HTTPS/SSL
- Use stronger database credentials
- Implement authentication for backend APIs

## Network Diagram

```
┌─────────────────────────────────────────────────────────┐
│ Ubuntu Server (192.168.5.74)                            │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Docker Network (face_recognition_network)       │  │
│  │                                                  │  │
│  │  ┌─────────────┐   ┌──────────────┐             │  │
│  │  │  Frontend   │   │   Backend    │  ┌────────┐ │  │
│  │  │  Nginx      │───│  Spring Boot │──│   DB   │ │  │
│  │  │  :3000      │   │  :8080       │  │PostgreSQL│
│  │  └─────────────┘   └──────────────┘  └────────┘ │  │
│  │                                                  │  │
│  └──────────────────────────────────────────────────┘  │
│        │                │                 │             │
│        ↓                ↓                 ↓             │
│   Port 3000      Port 8080          Port 5432         │
│   (0.0.0.0)      (0.0.0.0)          (0.0.0.0)         │
│        │                │                 │             │
└────────┼────────────────┼─────────────────┼─────────────┘
         │                │                 │
    Network accessible from any machine
    using 192.168.5.74:port
```

