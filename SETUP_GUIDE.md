# Employee Efficiency App - Setup Guide

## 🚀 Quick Start 

### Prerequisites

- ✅ Python 3.11 or higher
- ✅ Node.js 18 or higher  
- ✅ PostgreSQL 15+ 

---

## Step-by-Step Setup

### 1️⃣ Set Up PostgreSQL Database

**Option A: Install PostgreSQL Locally (Recommended)**

Download and install PostgreSQL:
- **Windows**: https://www.postgresql.org/download/windows/
- **Mac**: `brew install postgresql@15`
- **Linux**: `sudo apt-get install postgresql-15`

After installation:
```bash
# Create the database
createdb empeff

# Your DATABASE_URL will be:
# postgresql://postgres:YOUR_PASSWORD@localhost:5432/empeff
```

**Option B: Use a Cloud Database (Alternative)**

Sign up for a free PostgreSQL database:
- **Neon**: https://neon.tech (Free tier available)
- **Supabase**: https://supabase.com (Free tier available)
- **ElephantSQL**: https://www.elephantsql.com (Free tier available)

---

### 2️⃣ Backend Setup

```bash
# Navigate to backend folder
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On Mac/Linux:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
copy .env.example .env     # Windows
# cp .env.example .env     # Mac/Linux

# Edit .env file and update DATABASE_URL
# Use your editor to open backend/.env and modify:
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/empeff
SECRET_KEY=change-this-to-a-random-secret-key
```

**Start the backend server:**
```bash
uvicorn app.main:app --reload
```

✅ **Backend is running!**
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/health

---

### 3️⃣ Frontend Setup

Open a **NEW terminal window** (keep backend running):

```bash
# Navigate to frontend folder
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

✅ **Frontend is running!**
- App: http://localhost:5173

---

## 🧪 Testing Your Setup

1. **Open browser** to http://localhost:5173
2. **Click "Register"** to create an account
3. **Login** with your credentials
4. **Add employees** and explore the dashboard

---

## 🔧 Troubleshooting

### Backend Issues

**"ModuleNotFoundError"**
```bash
# Make sure virtual environment is activated
# You should see (venv) in your terminal prompt
venv\Scripts\activate
pip install -r requirements.txt
```

**"Connection refused" database error**
- Check PostgreSQL is running: `pg_isready`
- Verify DATABASE_URL in `.env` file
- Test connection: `psql -U postgres -d empeff`

**"Port 8000 already in use"**
```bash
# Find and kill the process (Windows)
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F

# Or use a different port
uvicorn app.main:app --reload --port 8001
```

### Frontend Issues

**"npm: command not found"**
- Install Node.js from https://nodejs.org/

**"Port 5173 already in use"**
```bash
# The dev server will automatically try the next available port
# Or specify a different port in vite.config.ts
```

**"Cannot connect to backend"**
- Ensure backend is running on http://localhost:8000
- Check browser console for CORS errors
- Verify axios baseURL configuration

---

## 📚 API Endpoints

### Health Check
```bash
GET http://localhost:8000/api/health
Response: {"status": "ok"}
```

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login (get token)
- `GET /api/auth/me` - Get current user

### Employees (Requires Authentication)
- `GET /api/employees/` - List all employees
- `POST /api/employees/` - Create employee
- `GET /api/employees/{id}` - Get employee
- `PATCH /api/employees/{id}` - Update employee
- `DELETE /api/employees/{id}` - Delete employee

---

## 🎯 Next Steps

1. **Change SECRET_KEY** in `.env` to something secure
2. **Explore the API docs** at http://localhost:8000/docs
3. **Run tests**: `cd backend && pytest`
4. **Build for production**: `cd frontend && npm run build`

---

## 💡 Tips

- Keep both terminal windows open (backend + frontend)
- Check backend logs for API errors
- Use browser DevTools (F12) to debug frontend issues
- Interactive API docs are your friend: http://localhost:8000/docs

---

## 🆘 Need Help?

- Check the main [README.md](./README.md) for detailed documentation
- Backend docs: [backend/README.md](./backend/README.md)
- Frontend docs: [frontend/README.md](./frontend/README.md)

Happy coding! 🎉
