# Docker Deployment Summary

## 📋 Files Created/Modified

### Created Files:
1. **`frontend/Dockerfile`** - Multi-stage build for React frontend with Nginx
2. **`frontend/nginx.conf`** - Nginx configuration for frontend with API proxying
3. **`frontend/.dockerignore`** - Excludes unnecessary files from build
4. **`backend/security-backend/Dockerfile`** - Multi-stage build for Spring Boot backend
5. **`backend/security-backend/.dockerignore`** - Excludes unnecessary files from build
6. **`integration/docker-compose.yml`** - Updated to expose ports on 0.0.0.0
7. **`integration/deploy.sh`** - Convenient deployment script
8. **`integration/DOCKER_DEPLOYMENT.md`** - Comprehensive documentation

### Modified Files:
1. **`frontend/src/services/api.ts`** - Added environment variable support
2. **`backend/security-backend/src/main/resources/application.properties`** - Environment variable support

## 🚀 Quick Start

### Option 1: Using the Deploy Script (Recommended)
```bash
cd /home/javi/dev/University/Semestre11/face_recognition_system/integration

# Make script executable
chmod +x deploy.sh

# Start everything
./deploy.sh start

# View logs
./deploy.sh logs

# Stop
./deploy.sh stop
```

### Option 2: Using Docker Compose Directly
```bash
cd /home/javi/dev/University/Semestre11/face_recognition_system/integration

# Build and start all services
docker-compose up -d --build

# View status
docker-compose ps

# View logs
docker-compose logs -f
```

## 🌐 Access Points

Once running, access from another computer using `192.168.5.74`:

- **Frontend UI**: http://192.168.5.74:3000
- **Backend API**: http://192.168.5.74:8080/api
- **PostgreSQL DB**: postgresql://192.168.5.74:5432/security_db
  - Username: postgres
  - Password: postgres

## 🔧 Key Features

✅ **Multi-stage Docker builds** - optimized image sizes
✅ **0.0.0.0 port bindings** - accessible from any machine on network
✅ **Health checks** - automatic service monitoring
✅ **Persistent database** - data survives container restarts
✅ **Auto-restart** - services restart if they crash
✅ **Environment variable configuration** - flexible deployment
✅ **Nginx reverse proxy** - frontend can reach backend through proxy
✅ **Docker networking** - services communicate via service names

## 📦 Container Specifications

### Frontend Container
- **Base Image**: nginx:alpine
- **Port**: 3000
- **Build**: React app built with react-scripts, served by Nginx
- **Proxy**: API requests routed to backend service

### Backend Container
- **Base Image**: eclipse-temurin:21-jdk-alpine
- **Port**: 8080
- **Build**: Gradle build, multi-stage to minimize image
- **Database**: PostgreSQL (service name: db)

### Database Container
- **Image**: postgres:15-alpine
- **Port**: 5432
- **Username**: postgres
- **Password**: postgres
- **Database**: security_db
- **Volume**: Persistent storage for data

## 💡 Important Notes

1. **Initial Build**: First startup takes several minutes (Gradle build, npm install)
2. **Backend Startup**: Takes ~30 seconds after container starts
3. **Port Mapping**: All ports are bound to `0.0.0.0:port` for network accessibility
4. **Network**: Services use Docker internal network (`face_recognition_network`)
5. **Credentials**: Default PostgreSQL password - change for production!

## 🆘 Troubleshooting

### Check service status
```bash
./deploy.sh status  # or docker-compose ps
```

### View logs for debugging
```bash
./deploy.sh logs backend
./deploy.sh logs frontend
./deploy.sh logs db
```

### Rebuild after code changes
```bash
./deploy.sh rebuild
```

### Access service shell
```bash
./deploy.sh shell backend
./deploy.sh shell frontend
./deploy.sh shell db
```

### Clean everything (⚠️ deletes database data)
```bash
./deploy.sh clean
```

## 📚 Documentation

For detailed configuration, troubleshooting, and production deployment information, see:
- [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)

