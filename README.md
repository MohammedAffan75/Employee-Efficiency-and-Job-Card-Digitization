# Employee Efficiency and Job Card Digitization

A full-stack web application for managing employee data and tracking efficiency metrics. Built with FastAPI, React, TypeScript, and PostgreSQL.

## 🎯 Features

- **Employee Management**: Create, update, and manage employee records
- **Authentication**: Secure JWT-based authentication system
- **Activity Tracking**: Track employee activities and work metrics
- **Job Card Management**: Manage job cards with approval workflows
- **Data Reporting**: View and analyze efficiency metrics with interactive dashboards
- **Role-Based Access**: Different permission levels for admin and staff
- **Responsive Design**: Modern UI with Tailwind CSS and React

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLModel** - SQL database ORM
- **PostgreSQL** - Relational database
- **Alembic** - Database migrations
- **JWT** - Authentication and authorization
- **Pydantic** - Data validation

### Frontend
- **React 18** - UI library
- **TypeScript** - Type-safe JavaScript
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS
- **React Router** - Client-side routing
- **Axios** - HTTP client
- **React Hook Form** - Form state management
- **Recharts** - Data visualization
- **Zod** - Schema validation

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Python** 3.11 or higher
- **Node.js** 18 or higher
- **PostgreSQL** 15 or higher

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd empeff
```

### 2. Set Up PostgreSQL Database

#### Option A: Local PostgreSQL Installation (Recommended)

**Windows**: Download from https://www.postgresql.org/download/windows/

**macOS**: 
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Linux**:
```bash
sudo apt-get update
sudo apt-get install postgresql-15
```

After installation, create the database:
```bash
createdb empeff
```

Your `DATABASE_URL` will be:
```
postgresql://postgres:YOUR_PASSWORD@localhost:5432/empeff
```

#### Option B: Cloud PostgreSQL (Alternative)

- [Neon](https://neon.tech) - Free tier available
- [Supabase](https://supabase.com) - Free tier available
- [ElephantSQL](https://www.elephantsql.com) - Free tier available

### 3. Backend Setup

```bash
# Navigate to backend folder
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
# Copy the example (if available) or create .env manually
# Windows:
copy .env.example .env
# macOS/Linux:
cp .env.example .env

# Edit .env with your settings:
# - DATABASE_URL: Your PostgreSQL connection string
# - SECRET_KEY: A random secret key for JWT
```

**Example .env file:**
```
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/empeff
SECRET_KEY=your-random-secret-key-here
APP_NAME=Employee Efficiency App
APP_VERSION=1.0.0
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

### 4. Database Migrations

Run migrations to set up the database schema:

```bash
# From the backend folder
alembic upgrade head
```

(Optional) To seed test data:
```bash
python seed_users.py
```

### 5. Start the Backend Server

```bash
# From the backend folder (with virtual environment activated)
uvicorn app.main:app --reload
```

✅ Backend is running at:
- API: http://localhost:8000
- Interactive API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/health

### 6. Frontend Setup

Open a **NEW terminal window** (keep backend running):

```bash
# Navigate to frontend folder
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

✅ Frontend is running at:
- App: http://localhost:5173

## 📁 Project Structure

```
empeff/
├── backend/                 # FastAPI backend application
│   ├── app/
│   │   ├── main.py         # FastAPI app initialization
│   │   ├── models.py       # Database models
│   │   ├── schemas.py      # Request/response schemas
│   │   ├── auth.py         # Authentication logic
│   │   ├── routes/         # API endpoints
│   │   ├── services/       # Business logic
│   │   └── core/           # Core configuration
│   ├── alembic/            # Database migrations
│   ├── tests/              # Backend tests
│   ├── requirements.txt    # Python dependencies
│   └── pytest.ini          # Test configuration
│
├── frontend/               # React TypeScript frontend
│   ├── src/
│   │   ├── App.tsx         # Main app component
│   │   ├── main.tsx        # Entry point
│   │   ├── components/     # Reusable React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API integration
│   │   ├── hooks/          # Custom React hooks
│   │   ├── context/        # React context providers
│   │   ├── types/          # TypeScript type definitions
│   │   └── utils/          # Utility functions
│   ├── package.json        # NPM dependencies
│   ├── vite.config.ts      # Vite configuration
│   └── tailwind.config.js  # Tailwind CSS config
│
└── README.md               # This file
```

## 🔐 Authentication

The application uses JWT (JSON Web Tokens) for authentication:

1. **Login**: Send credentials to `/api/auth/login`
2. **Token Received**: Use token in `Authorization: Bearer <token>` header
3. **Access Protected Routes**: Include token in all requests to protected endpoints
4. **Token Refresh**: Tokens can be refreshed at `/api/auth/refresh`

## 📚 API Endpoints

The API documentation is available at http://localhost:8000/docs when the backend is running.

Main endpoint groups:
- `/api/auth` - Authentication endpoints
- `/api/employees` - Employee management
- `/api/activity-codes` - Activity tracking
- `/api/job-cards` - Job card management
- `/api/reporting` - Analytics and reports
- `/api/health` - Health check

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py
```

### Frontend Tests

```bash
cd frontend

# Lint code
npm run lint

# Build for production
npm run build

# Preview production build
npm run preview
```

## 🔄 Database Migrations

### Creating a New Migration

```bash
cd backend

# Auto-generate migration (detects model changes)
alembic revision --autogenerate -m "Description of changes"

# Review the generated migration in alembic/versions/

# Apply the migration
alembic upgrade head
```

### Reverting Migrations

```bash
cd backend

# Revert to previous migration
alembic downgrade -1

# Revert to specific migration
alembic downgrade <revision_id>
```


## 🐛 Troubleshooting

### Backend won't start
- Ensure PostgreSQL is running
- Check `DATABASE_URL` in `.env`
- Run migrations: `alembic upgrade head`

### Frontend can't connect to backend
- Verify backend is running on http://localhost:8000
- Check `CORS_ORIGINS` includes frontend URL
- Check browser console for CORS errors

### Database connection errors
- Verify PostgreSQL is running
- Check database credentials in `.env`
- Ensure database exists: `createdb empeff`

## 📝 Environment Variables

Create a `.env` file in the `backend` folder:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/empeff

# Security
SECRET_KEY=your-secret-key-here-change-in-production

# Application
APP_NAME=Employee Efficiency App
APP_VERSION=1.0.0

# CORS
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# Optional: Add other configuration as needed
DEBUG=False
```

## 👥 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request


## 🆘 Support

For issues, questions, or suggestions:
1. Check existing issues in the repository
2. Create a new issue with a clear description
3. Include relevant error messages and steps to reproduce

## 🎓 Learning Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Tailwind CSS](https://tailwindcss.com/)
- [SQLModel](https://sqlmodel.tiangolo.com/)

---

**Happy coding!** 🚀
