# 🚀 Quick Start Guide - Windows

## Step 1: Start Docker Desktop

Your error indicates Docker Desktop is not running. Follow these steps:

### Option A: Start Docker Desktop GUI (Recommended)

1. Press `Windows Key` and search for **"Docker Desktop"**
2. Click to launch Docker Desktop
3. Wait for the Docker icon in the system tray (bottom-right) to become steady
4. You should see "Docker Desktop is running" when you click the icon

### Option B: Start Docker Service via PowerShell

1. Open **PowerShell as Administrator**:
   - Press `Windows Key`
   - Type "PowerShell"
   - Right-click "Windows PowerShell"
   - Select "Run as administrator"

2. Start the Docker service:
   ```powershell
   Start-Service -Name com.docker.service
   ```

3. Verify Docker is running:
   ```powershell
   docker version
   docker info
   ```

## Step 2: Verify Docker is Working

Once Docker Desktop is running, test it:

```cmd
docker version
```

You should see both **Client** and **Server** information without errors.

## Step 3: Start Your Application

Now you can start the Loriaa AI backend:

```cmd
cd D:\Git_Repo\loriaa-ai-backend
docker-compose down
docker-compose up --build -d
```

## Step 4: Check Status

```cmd
docker-compose ps
docker-compose logs -f backend
```

## Step 5: Seed Database

```cmd
docker-compose exec backend python scripts/seed_data.py
```

## Step 6: Access the Application

- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Common Issues

### WSL 2 Backend Issues

If you're using WSL 2 backend, ensure WSL is running:

```cmd
wsl --status
wsl -l -v
```

If WSL is not running or needs update:

```cmd
wsl --update
wsl --set-default-version 2
```

### Port Conflicts

If ports 5432 or 8000 are already in use:

```cmd
# Find what's using the port
netstat -ano | findstr :8000
netstat -ano | findstr :5432

# Kill the process (replace <PID> with actual Process ID)
taskkill /PID <PID> /F
```

### Docker Desktop Installation

If Docker Desktop is not installed:

1. Download from: https://www.docker.com/products/docker-desktop
2. Install with WSL 2 backend enabled
3. Restart your computer
4. Start Docker Desktop

## Troubleshooting Checklist

- [ ] Docker Desktop is installed
- [ ] Docker Desktop is running (check system tray icon)
- [ ] `docker version` shows both Client and Server info
- [ ] Ports 8000 and 5432 are available
- [ ] WSL 2 is installed and running (if using WSL backend)
- [ ] `.env` file exists in project root

## Need Help?

Check the main [README.md](README.md) for detailed troubleshooting and documentation.

