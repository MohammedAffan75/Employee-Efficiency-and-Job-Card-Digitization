# 🎨 Frontend Setup Instructions

Employee Efficiency Tracking System - React + Vite + TypeScript + TailwindCSS

---

## ✅ What's Already Set Up

### **1. Project Structure**
```
frontend/
├── src/
│   ├── components/       ✅ Layout, PrivateRoute
│   ├── context/          ✅ AuthContext (updated)
│   ├── hooks/            ✅ useAuth
│   ├── layouts/          ✅ Created (empty)
│   ├── pages/            ✅ Dashboard, Employees, Login, Register
│   ├── services/         ✅ api, authService, jobCardService
│   ├── types/            ✅ TypeScript interfaces
│   ├── App.tsx           ✅ Routing configured
│   ├── main.tsx          ✅ Entry point
│   └── index.css         ✅ Tailwind styles
├── tailwind.config.js    ✅ Industrial grey-blue theme
├── package.json          ✅ Updated with new dependencies
└── .env.example          ✅ API configuration
```

### **2. Dependencies Added**
- ✅ `react-hook-form` - Form validation
- ✅ `zod` - Schema validation
- ✅ `recharts` - Charts and graphs
- ✅ `@headlessui/react` - UI components
- ✅ `react-hot-toast` - Notifications

### **3. Tailwind Theme**
- ✅ Industrial grey-blue color palette
- ✅ Inter font family
- ✅ Custom shadows and styles

### **4. Auth Integration**
- ✅ AuthContext updated to use Employee type
- ✅ Login using EC Number (not email)
- ✅ JWT token management
- ✅ Auth service with axios interceptors

---

## 🚀 Installation Steps

### **Step 1: Install Dependencies**

Open terminal in the `frontend/` directory:

```bash
cd frontend
npm install
```

**This will install:**
- All existing dependencies (react, axios, lucide-react, react-router-dom)
- Newly added packages (react-hook-form, zod, recharts, @headlessui/react, react-hot-toast)

### **Step 2: Create .env File**

Create a `.env` file in the `frontend/` directory:

```bash
# Copy from example
copy .env.example .env

# Or create manually with this content:
VITE_API_URL=http://localhost:8000/api
VITE_ENV=development
```

### **Step 3: Start Development Server**

```bash
npm run dev
```

**Expected output:**
```
  VITE v5.0.8  ready in 500 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

### **Step 4: Open in Browser**

Visit: **http://localhost:5173**

You should see the login page!

---

## 🔗 Connecting to Backend

### **Prerequisites**
1. ✅ Backend running at `http://localhost:8000`
2. ✅ PostgreSQL database running
3. ✅ CORS configured in backend

### **Test Login**

If you created an admin user in the backend:

```
EC Number: ADMIN001
Password: admin123
```

If successful, you'll be redirected to `/dashboard`!

---

## 🐛 Troubleshooting

### **Issue: TypeScript Errors**

All the TypeScript errors you see are because dependencies aren't installed yet.

**Solution:**
```bash
npm install
```

### **Issue: Cannot connect to API**

```
Error: Network Error
```

**Solution:**
1. Check backend is running: `http://localhost:8000/docs`
2. Check `.env` has correct API URL
3. Check CORS is configured in backend

### **Issue: Login fails with 401**

```
Error: Unauthorized
```

**Solution:**
1. Create test admin user in backend (see backend/QUICKSTART.md)
2. Use correct EC number (e.g., ADMIN001)
3. Use correct password

### **Issue: Port 5173 already in use**

```
Error: Port 5173 is already in use
```

**Solution:**
```bash
# Use different port
npm run dev -- --port 3000
```

---

## 📁 File Structure Details

### **Created Files**

| File | Purpose |
|------|---------|
| `.env.example` | Environment variable template |
| `src/types/index.ts` | TypeScript interfaces matching backend |
| `src/services/api.ts` | Axios instance with interceptors |
| `src/services/authService.ts` | Authentication service |
| `src/services/jobCardService.ts` | JobCard API calls |
| `src/hooks/useAuth.ts` | Auth hook |

### **Updated Files**

| File | Changes |
|------|---------|
| `package.json` | Added 5 new dependencies |
| `tailwind.config.js` | Industrial grey-blue theme + Inter font |
| `index.html` | Added Inter font import |
| `src/context/AuthContext.tsx` | Updated to use Employee type + authService |
| `src/pages/Login.tsx` | Updated to use EC Number |

---

## 🎨 Theme Colors

The app uses an industrial grey-blue theme:

```javascript
Primary (Blue-Grey): #627d98
Secondary (Neutral Grey): #718096
Accent (Teal): #38b2ac
Success (Green): #22c55e
Warning (Orange): #f59e0b
Danger (Red): #ef4444
```

Use in Tailwind:
```html
<div className="bg-primary-500 text-white">
  Primary Button
</div>
```

---

## 📖 Next Steps

### **1. Test the Application**

```bash
# Start backend (in backend folder)
cd ../backend
venv\Scripts\activate
uvicorn app.main:app --reload

# Start frontend (in frontend folder)
cd ../frontend
npm run dev
```

### **2. Login and Explore**

- Visit http://localhost:5173
- Login with ADMIN001 / admin123
- Check Dashboard page
- Check Employees page

### **3. Development**

The app has:
- ✅ Hot reload enabled
- ✅ TypeScript type checking
- ✅ Tailwind CSS
- ✅ React Router v6
- ✅ Auth context
- ✅ API service layer

### **4. Build for Production**

```bash
npm run build
```

Output will be in `dist/` folder.

---

## 🔧 Available Scripts

```bash
# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

---

## 📚 Documentation

- **Backend API**: http://localhost:8000/docs
- **Backend Integration Guide**: `backend/FRONTEND_INTEGRATION_GUIDE.md`
- **Backend Deployment**: `backend/DEPLOYMENT_COMPLETE.md`

---

## ✨ Features Ready to Use

- ✅ **Authentication** - Login with EC number
- ✅ **Protected Routes** - Role-based access
- ✅ **API Integration** - Axios with interceptors
- ✅ **Toast Notifications** - react-hot-toast
- ✅ **Form Handling** - react-hook-form + zod
- ✅ **Charts** - recharts library
- ✅ **UI Components** - @headlessui/react
- ✅ **Icons** - lucide-react
- ✅ **Styling** - Tailwind with custom theme

---

Your frontend is ready to run! 🎉

Run `npm install` then `npm run dev` to get started!
