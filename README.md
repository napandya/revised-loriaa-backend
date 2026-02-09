# 🤖 Loriaa AI Backend

Comprehensive FastAPI backend for the Loriaa AI voice bot platform with AI-powered features, real-time call tracking, and intelligent knowledge base management.

## ✨ Features

- 🔐 **JWT Authentication** - Secure user authentication with OAuth2 and JWT tokens
- 🤖 **Bot Management System** - Create, configure, and manage multiple AI voice bots
- 📞 **Call Logs Tracking** - Track and analyze inbound/outbound call records
- 👥 **Team Management** - Manage team members with role-based access
- 💰 **Billing Dashboard** - Real-time cost tracking and billing analytics
- 🧠 **Vector-based Knowledge Base (RAG)** - OpenAI embeddings with pgvector for semantic search
- 📊 **Dashboard Metrics** - Comprehensive analytics and performance metrics
- 🐳 **Docker Support** - Full containerization with Docker Compose
- 📚 **Auto-generated API Documentation** - Interactive Swagger UI and ReDoc

## 🛠 Tech Stack

- **FastAPI** - Modern, fast web framework for building APIs
- **PostgreSQL with pgvector** - Vector similarity search for RAG
- **SQLAlchemy 2.0** - SQL toolkit and ORM
- **JWT Authentication** - Secure token-based authentication
- **OpenAI Embeddings** - Text embeddings for semantic search
- **Docker & Docker Compose** - Containerization and orchestration
- **Pydantic** - Data validation using Python type annotations

## 📋 Prerequisites

Choose one of the following:

**Option 1: Docker (Recommended)**
- Docker 20.10+
- Docker Compose 1.29+

**Option 2: Manual Setup**
- Python 3.11+
- PostgreSQL 15+ with pgvector extension

## 🚀 Quick Start with Docker

### 1. Clone the repository

```bash
git clone https://github.com/napandya/loriaa-ai-backend.git
cd loriaa-ai-backend
```

### 2. Create environment file

```bash
cp .env.example .env
```

Edit `.env` and update the values (especially `OPENAI_API_KEY` if using knowledge base features):

```env
DATABASE_URL=postgresql://loriaa_user:loriaa_pass@postgres:5432/loriaa_db
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
OPENAI_API_KEY=sk-your-openai-api-key-here
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000","http://localhost:5174"]
```

### 3. Start services with Docker Compose

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database with pgvector extension (port 5432)
- FastAPI backend application (port 8000)

### 4. Seed the database

```bash
docker-compose exec backend python scripts/seed_data.py
```

### 5. Access the API

- **API Base URL**: http://localhost:8000
- **Swagger UI (Interactive Docs)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🔧 Manual Setup (without Docker)

### 1. Install PostgreSQL with pgvector

```bash
# On Ubuntu/Debian
sudo apt-get update
sudo apt-get install postgresql-15 postgresql-contrib

# Install pgvector
sudo apt-get install postgresql-15-pgvector

# Or install from source
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

### 2. Create database

```bash
sudo -u postgres psql

# In PostgreSQL shell:
CREATE DATABASE loriaa_db;
CREATE USER loriaa_user WITH PASSWORD 'loriaa_pass';
GRANT ALL PRIVILEGES ON DATABASE loriaa_db TO loriaa_user;
\c loriaa_db
CREATE EXTENSION vector;
\q
```

### 3. Install Python dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 5. Create tables and seed database

```bash
python scripts/seed_data.py
```

### 6. Start the server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 📚 API Endpoints Documentation

### Authentication

- `POST /api/v1/auth/register` - Register a new user
- `POST /api/v1/auth/login` - Login and get JWT token
- `GET /api/v1/auth/me` - Get current user profile

### Bots

- `GET /api/v1/bots` - Get all bots (with pagination, search)
- `POST /api/v1/bots` - Create a new bot
- `GET /api/v1/bots/{bot_id}` - Get bot details
- `PUT /api/v1/bots/{bot_id}` - Update a bot
- `DELETE /api/v1/bots/{bot_id}` - Delete a bot

### Call Logs

- `GET /api/v1/call-logs` - Get all call logs (with pagination, search)
- `POST /api/v1/call-logs` - Create a new call log
- `GET /api/v1/call-logs/{log_id}` - Get call log details

### Teams

- `GET /api/v1/teams` - Get all team members
- `POST /api/v1/teams` - Create a new team member
- `PUT /api/v1/teams/{member_id}` - Update a team member
- `DELETE /api/v1/teams/{member_id}` - Delete a team member

### Billing

- `GET /api/v1/billing/current` - Get current month billing stats
- `GET /api/v1/billing/history` - Get billing history
- `GET /api/v1/billing/stats?month=YYYY-MM` - Get stats for specific month

### Knowledge Base

- `POST /api/v1/kb/documents` - Upload a document (with OpenAI embeddings)
- `GET /api/v1/kb/documents?bot_id={bot_id}` - Get all documents for a bot
- `DELETE /api/v1/kb/documents/{doc_id}` - Delete a document
- `POST /api/v1/kb/query` - Query knowledge base with vector similarity search
- `POST /api/v1/kb/chat` - RAG-based chat with context from knowledge base

### Dashboard

- `GET /api/v1/dashboard/metrics` - Get dashboard overview metrics
- `GET /api/v1/dashboard/analytics` - Get analytics with time-series data

## 📁 Project Structure

```
loriaa-ai-backend/
├── app/
│   ├── api/                    # API routes
│   │   ├── v1/
│   │   │   ├── auth.py        # Authentication endpoints
│   │   │   ├── bots.py        # Bot management
│   │   │   ├── call_logs.py   # Call log tracking
│   │   │   ├── teams.py       # Team management
│   │   │   ├── billing.py     # Billing endpoints
│   │   │   ├── knowledge_base.py  # RAG and vector search
│   │   │   └── dashboard.py   # Dashboard metrics
│   │   └── deps.py            # Shared dependencies
│   ├── core/                  # Core utilities
│   │   ├── config.py          # Application settings
│   │   ├── security.py        # Security utilities
│   │   └── embeddings.py      # OpenAI embeddings
│   ├── models/                # SQLAlchemy models
│   │   ├── user.py
│   │   ├── bot.py
│   │   ├── call_log.py
│   │   ├── team.py
│   │   ├── knowledge_base.py
│   │   └── billing.py
│   ├── schemas/               # Pydantic schemas
│   │   ├── user.py
│   │   ├── bot.py
│   │   ├── call_log.py
│   │   ├── team.py
│   │   ├── knowledge_base.py
│   │   └── billing.py
│   ├── database.py            # Database setup
│   └── main.py                # FastAPI application
├── scripts/
│   └── seed_data.py           # Database seeding script
├── .env.example               # Environment variables template
├── .gitignore
├── docker-compose.yml         # Docker Compose configuration
├── Dockerfile                 # Docker image definition
├── init.sql                   # PostgreSQL initialization
├── requirements.txt           # Python dependencies
└── README.md
```

## 💻 Frontend Integration Examples

### Login Example

```typescript
// Using fetch
const login = async (email: string, password: string) => {
  const formData = new FormData();
  formData.append('username', email);  // OAuth2 uses 'username' field
  formData.append('password', password);
  
  const response = await fetch('http://localhost:8000/api/v1/auth/login', {
    method: 'POST',
    body: formData,
  });
  
  const data = await response.json();
  localStorage.setItem('token', data.access_token);
  return data;
};

// Using axios
import axios from 'axios';

const login = async (email: string, password: string) => {
  const formData = new URLSearchParams();
  formData.append('username', email);
  formData.append('password', password);
  
  const response = await axios.post(
    'http://localhost:8000/api/v1/auth/login',
    formData
  );
  
  localStorage.setItem('token', response.data.access_token);
  return response.data;
};
```

### Authenticated Request Example

```typescript
const getBots = async () => {
  const token = localStorage.getItem('token');
  
  const response = await fetch('http://localhost:8000/api/v1/bots', {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  
  return await response.json();
};
```

## 🧠 Knowledge Base Usage

### Upload a Document

```bash
curl -X POST "http://localhost:8000/api/v1/kb/documents" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bot_id": "your-bot-uuid",
    "title": "Rent Payment Policy",
    "content": "Our rent payment policy requires payment by the 5th of each month...",
    "metadata": {"category": "policy"}
  }'
```

### Query with Vector Search

```bash
curl -X POST "http://localhost:8000/api/v1/kb/query" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bot_id": "your-bot-uuid",
    "query": "What is the rent payment deadline?",
    "top_k": 5
  }'
```

## 🔐 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://loriaa_user:loriaa_pass@localhost:5432/loriaa_db` |
| `SECRET_KEY` | JWT secret key | `dev-secret-key-change-in-production` |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT expiration time | `30` |
| `OPENAI_API_KEY` | OpenAI API key for embeddings | Required for KB features |
| `CORS_ORIGINS` | Allowed CORS origins (JSON array) | `["http://localhost:5173"]` |

## 🐛 Troubleshooting

### Docker Desktop Not Running (Windows)

**Error**: `unable to get image 'loriaa-ai-backend-backend': error during connect: open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.`

**Solution**:

1. **Start Docker Desktop**:
   - Open Docker Desktop from the Start Menu
   - Wait for Docker to fully start (whale icon should be steady in system tray)
   - You should see "Docker Desktop is running" in the UI

2. **Verify Docker is running**:
   ```cmd
   docker version
   docker info
   ```

3. **Check Docker service** (PowerShell as Administrator):
   ```powershell
   Get-Service -Name com.docker.service
   # If stopped, start it:
   Start-Service -Name com.docker.service
   ```

4. **If using WSL 2 backend**, verify WSL is running:
   ```cmd
   wsl --status
   wsl -l -v
   ```

5. **Restart Docker Desktop**:
   - Right-click Docker icon in system tray → Quit Docker Desktop
   - Wait 10 seconds
   - Start Docker Desktop again

6. **After Docker is running**, try again:
   ```cmd
   docker-compose down
   docker-compose up --build -d
   ```

### Uvicorn Command Not Found

**Error**: `uvicorn : The term 'uvicorn' is not recognized as the name of a cmdlet, function, script file, or operable program.`

This error means uvicorn is not installed or Python is not in your PATH. You have two options:

**Option A: Use Docker (Recommended - Already Working!)**

Your application is already running in Docker! No need to install Python locally.

```cmd
# Check if containers are running
docker-compose ps

# View logs
docker-compose logs -f backend

# Restart if needed
docker-compose restart backend
```

Access your API at: http://localhost:8000/docs

**Option B: Install Python and Dependencies Locally**

If you want to run without Docker:

1. **Install Python 3.11+**:
   - Download from: https://www.python.org/downloads/
   - During installation, check "Add Python to PATH"
   - Restart your terminal after installation

2. **Verify Python installation**:
   ```cmd
   python --version
   # or
   py --version
   ```

3. **Create and activate virtual environment**:
   ```cmd
   cd D:\Git_Repo\loriaa-ai-backend
   python -m venv venv
   venv\Scripts\activate
   ```

4. **Install dependencies**:
   ```cmd
   pip install -r requirements.txt
   ```

5. **Set up local PostgreSQL** (or use Docker for just the database):
   ```cmd
   # Option 1: Use Docker for database only
   docker-compose up -d postgres
   
   # Update .env to point to localhost
   # DATABASE_URL=postgresql://loriaa_user:loriaa_pass@localhost:5432/loriaa_db
   ```

6. **Run uvicorn**:
   ```cmd
   # From project root (not app folder!)
   cd D:\Git_Repo\loriaa-ai-backend
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Common Docker Issues

**Port already in use (5432 or 8000)**:
```cmd
# Find process using port 5432 (PostgreSQL)
netstat -ano | findstr :5432

# Find process using port 8000 (Backend)
netstat -ano | findstr :8000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

**Database connection errors**:
```bash
# Check if PostgreSQL container is healthy
docker-compose ps

# View database logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

**Backend container crashes**:
```bash
# View backend logs
docker-compose logs backend

# Rebuild backend image
docker-compose up --build backend
```

**Permission issues (Windows)**:
```cmd
# Run PowerShell as Administrator and restart Docker
Restart-Service -Name com.docker.service -Force
```

## 🛠 Development Commands

### View logs

```bash
docker-compose logs -f backend
```

### Restart services

```bash
docker-compose restart
```

### Stop services

```bash
docker-compose down
```

### Reset database

```bash
docker-compose down -v
docker-compose up -d
docker-compose exec backend python scripts/seed_data.py
```

### Run tests

```bash
# With Docker
docker-compose exec backend pytest

# Without Docker
pytest
```

## 🚀 Deployment

### Production Environment Variables

For production, make sure to:

1. Generate a secure secret key:
```bash
openssl rand -hex 32
```

2. Set strong database credentials
3. Configure proper CORS origins
4. Set `OPENAI_API_KEY` if using knowledge base features

### Security Considerations

- Never commit `.env` file to version control
- Use strong passwords for database and secret keys
- Enable HTTPS in production
- Implement rate limiting for API endpoints
- Regular security updates for dependencies

## 🔑 Default Credentials

After seeding the database:

```
Email: demo@loriaa.ai
Password: password123
```

## 📖 API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide interactive API documentation where you can test endpoints directly.

## 📝 License

MIT License

## 👤 Author

**Nandan Pandya**

- Email: pandyanandan@gmail.com
- GitHub: [@napandya](https://github.com/napandya)

**Daniel Twito**

- Email: Daniel@loriaa.ai
- GitHub: [@outsider8u](https://github.com/outsider8u)

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/napandya/loriaa-ai-backend/issues).

## ⭐ Show your support

Give a ⭐️ if this project helped you!

---

**Built with ❤️ using FastAPI and modern Python tools**
