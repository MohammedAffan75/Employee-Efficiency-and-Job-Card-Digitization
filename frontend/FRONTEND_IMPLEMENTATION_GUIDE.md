# 🎨 Frontend Implementation Guide

Complete implementation guide for the Employee Efficiency Tracking System frontend.

---

## ✅ COMPLETED (Phase 1)

### **1. Authentication & Role Handling** ✅

**Files Created:**
- `src/utils/jwt.ts` - JWT decoding utilities
- `src/services/authService.ts` - Enhanced with role extraction
- `src/components/ProtectedRoute.tsx` - Role-based route protection
- `src/hooks/useRole.ts` - Role management hook
- `src/context/AuthContext.tsx` - Updated (already existed)

**Features:**
- ✅ JWT token decoding with role extraction
- ✅ Token expiration checking
- ✅ Role-based route redirection
- ✅ Persistent localStorage session
- ✅ Auto-logout on token expiry

### **2. Global Layouts & Navigation** ✅

**Files Created:**
- `src/components/Sidebar.tsx` - Role-based navigation
- `src/components/Header.tsx` - User info + logout
- `src/layouts/OperatorLayout.tsx` - Operator layout wrapper
- `src/layouts/SupervisorLayout.tsx` - Supervisor layout wrapper
- `src/layouts/AdminLayout.tsx` - Admin layout wrapper

**Features:**
- ✅ Responsive sidebar with role-specific links
- ✅ Header with user info and logout
- ✅ Consistent layout across all roles
- ✅ Tailwind industrial grey-blue theme

### **3. Services & Types** ✅

**Files Created:**
- `src/services/api.ts` - Axios instance with interceptors
- `src/services/authService.ts` - Complete auth service
- `src/services/jobCardService.ts` - JobCard CRUD operations
- `src/types/index.ts` - All TypeScript interfaces

**Features:**
- ✅ Automatic JWT injection
- ✅ Global error handling
- ✅ 401 auto-logout
- ✅ Toast notifications on errors

---

## 📋 TODO (Phase 2) - Operator Pages

### **Operator Dashboard**
Create: `src/pages/operator/OperatorDashboard.tsx`

```typescript
import { useEffect, useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import { EfficiencyMetrics, JobCard } from '../../types';

const OperatorDashboard = () => {
  const { user } = useAuth();
  const [metrics, setMetrics] = useState<EfficiencyMetrics | null>(null);
  const [recentJobs, setRecentJobs] = useState<JobCard[]>([]);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    // GET /efficiency/{employee_id}?start=&end=
    const end = new Date().toISOString().split('T')[0];
    const start = new Date(Date.now() - 30*24*60*60*1000).toISOString().split('T')[0];
    
    const [effResponse, jobsResponse] = await Promise.all([
      api.get(`/efficiency/${user?.id}?start=${start}&end=${end}`),
      api.get(`/jobcards?employee_id=${user?.id}&limit=5`)
    ]);

    setMetrics(effResponse.data);
    setRecentJobs(jobsResponse.data);
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-secondary-900">Dashboard</h1>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KPICard title="Time Efficiency" value={metrics?.time_efficiency} />
        <KPICard title="Quantity Efficiency" value={metrics?.quantity_efficiency} />
        <KPICard title="Task Efficiency" value={metrics?.task_efficiency} />
        <KPICard title="AWC %" value={metrics?.awc_pct} />
      </div>

      {/* Recent Job Cards */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Recent Job Cards</h2>
        <table className="min-w-full">
          {/* Table implementation */}
        </table>
      </div>
    </div>
  );
};
```

### **JobCard Form**
Create: `src/pages/operator/JobCardForm.tsx`

**Features Needed:**
- React Hook Form + Zod validation
- Dynamic field rendering based on efficiency_type
- AWC checkbox shows ActivityDesc field
- Dropdown for WorkOrder, Machine, ActivityCode
- Submit to POST `/jobcards`

```typescript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const jobCardSchema = z.object({
  work_order_id: z.number(),
  machine_id: z.number(),
  activity_code_id: z.number().optional(),
  activity_desc: z.string(),
  qty: z.number().positive(),
  actual_hours: z.number().positive(),
  status: z.enum(['C', 'IC']),
  entry_date: z.string(),
});

const JobCardForm = () => {
  const { register, handleSubmit, watch, formState: { errors } } = useForm({
    resolver: zodResolver(jobCardSchema)
  });

  const onSubmit = async (data) => {
    await api.post('/jobcards', data);
    toast.success('Job card created!');
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      {/* Form fields */}
    </form>
  );
};
```

### **JobCard List**
Create: `src/pages/operator/JobCardList.tsx`

- Table with sorting/filtering
- Status badges (C/IC)
- Flags indicator
- Edit/Delete actions

---

## 📋 TODO (Phase 3) - Supervisor Pages

### **Supervisor Dashboard**
Create: `src/pages/supervisor/SupervisorDashboard.tsx`

**API:** GET `/reporting/dashboard/summary?team_id={team}`

**Components:**
- Team KPI cards (averages)
- Bar chart: Efficiency by operator (use `recharts`)
- Table: Employee list with efficiencies

### **Assignment Panel**
Create: `src/pages/supervisor/AssignmentPanel.tsx`

**API:** POST `/supervisor/assign`

**Features:**
- Multi-select operators
- Toggle: Manual hours vs Auto-split
- Confirmation modal (@headlessui/react)

### **Validation Panel**
Create: `src/pages/supervisor/ValidationPanel.tsx`

**API:** 
- GET `/supervisor/validations?resolved=false`
- PATCH `/supervisor/validations/{id}/resolve`

**Features:**
- Table of unresolved flags
- Resolve button with comment modal
- Filter by flag_type

### **Reports Page**
Create: `src/pages/supervisor/ReportsPage.tsx`

**API:** GET `/reporting/report/monthly?month=YYYY-MM`

**Features:**
- Month picker
- Download CSV button
- Preview table

---

## 📋 TODO (Phase 4) - Admin Pages

### **Activity Codes Page**
Create: `src/pages/admin/ActivityCodesPage.tsx`

**CRUD Operations:**
- GET `/activity-codes`
- POST `/activity-codes`
- PATCH `/activity-codes/{id}`
- DELETE `/activity-codes/{id}`

**Components:**
- DataTable with actions
- Add/Edit Modal (@headlessui/react Dialog)
- Delete confirmation

### **Machines Page**
Create: `src/pages/admin/MachinesPage.tsx`

Similar CRUD structure as Activity Codes.

### **Employees Page**
Create: `src/pages/admin/EmployeesPage.tsx`

**Features:**
- List all employees
- Toggle Active/Inactive
- Change role dropdown
- Search/filter

---

## 📋 TODO (Phase 5) - Charts & Analytics

### **Install @hookform/resolvers**
```bash
npm install @hookform/resolvers
```

### **Team Dashboard Charts**
Use `recharts`:

```typescript
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

<ResponsiveContainer width="100%" height={300}>
  <BarChart data={teamData}>
    <XAxis dataKey="employee_name" />
    <YAxis />
    <Tooltip />
    <Bar dataKey="time_efficiency" fill="#627d98" />
    <Bar dataKey="qty_efficiency" fill="#38b2ac" />
  </BarChart>
</ResponsiveContainer>
```

---

## 📋 TODO (Phase 6) - Update App.tsx Routing

**Replace current `App.tsx` with:**

```typescript
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';

// Layouts
import OperatorLayout from './layouts/OperatorLayout';
import SupervisorLayout from './layouts/SupervisorLayout';
import AdminLayout from './layouts/AdminLayout';

// Operator Pages
import OperatorDashboard from './pages/operator/OperatorDashboard';
import JobCardForm from './pages/operator/JobCardForm';
import JobCardList from './pages/operator/JobCardList';

// Supervisor Pages
import SupervisorDashboard from './pages/supervisor/SupervisorDashboard';
import AssignmentPanel from './pages/supervisor/AssignmentPanel';
import ValidationPanel from './pages/supervisor/ValidationPanel';
import ReportsPage from './pages/supervisor/ReportsPage';

// Admin Pages
import ActivityCodesPage from './pages/admin/ActivityCodesPage';
import MachinesPage from './pages/admin/MachinesPage';
import EmployeesPage from './pages/admin/EmployeesPage';

import { RoleEnum } from './types';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Toaster position="top-right" />
        <Routes>
          <Route path="/login" element={<Login />} />

          {/* Operator Routes */}
          <Route
            path="/operator"
            element={
              <ProtectedRoute allowedRoles={[RoleEnum.OPERATOR]}>
                <OperatorLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<OperatorDashboard />} />
            <Route path="jobcards" element={<JobCardList />} />
            <Route path="jobcards/new" element={<JobCardForm />} />
          </Route>

          {/* Supervisor Routes */}
          <Route
            path="/supervisor"
            element={
              <ProtectedRoute allowedRoles={[RoleEnum.SUPERVISOR]}>
                <SupervisorLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<SupervisorDashboard />} />
            <Route path="assignments" element={<AssignmentPanel />} />
            <Route path="validations" element={<ValidationPanel />} />
            <Route path="reports" element={<ReportsPage />} />
          </Route>

          {/* Admin Routes */}
          <Route
            path="/admin"
            element={
              <ProtectedRoute allowedRoles={[RoleEnum.ADMIN]}>
                <AdminLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/admin/employees" />} />
            <Route path="activity-codes" element={<ActivityCodesPage />} />
            <Route path="machines" element={<MachinesPage />} />
            <Route path="employees" element={<EmployeesPage />} />
          </Route>

          {/* Default redirect */}
          <Route path="/" element={<Navigate to="/login" />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
```

---

## 📋 TODO (Phase 7) - Docker & Deployment

### **Dockerfile**
Create: `frontend/Dockerfile`

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### **nginx.conf**
Create: `frontend/nginx.conf`

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend:8000;
    }
}
```

### **docker-compose.yml** (Root)
Update root `docker-compose.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: empeff
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:postgres@db:5432/empeff
      SECRET_KEY: your-secret-key-change-in-production
    depends_on:
      - db

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    environment:
      VITE_API_URL: http://localhost:8000/api
    depends_on:
      - backend

volumes:
  postgres_data:
```

---

## 🧪 TODO (Phase 8) - Testing

### **Install Testing Dependencies**
```bash
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom
```

### **vitest.config.ts**
```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
  },
});
```

### **Sample Test: Login.test.tsx**
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import Login from '../pages/Login';

vi.mock('../services/authService');

describe('Login Page', () => {
  it('renders login form', () => {
    render(<Login />);
    expect(screen.getByPlaceholderText(/EC Number/i)).toBeInTheDocument();
  });

  it('submits form with credentials', async () => {
    render(<Login />);
    // Test implementation
  });
});
```

---

## 🎯 Priority Implementation Order

1. ✅ **DONE: Auth & Layouts**
2. **Install dependencies**: `npm install`
3. **Create .env file**: Copy from `.env.example`
4. **Update App.tsx routing** (see Phase 6)
5. **Operator Dashboard** → Test with backend
6. **JobCard Form** → Essential for operators
7. **Supervisor Dashboard** → Team management
8. **Admin CRUD pages** → Master data
9. **Charts & Analytics** → Visual insights
10. **Docker deployment** → Production ready

---

## 📚 Component Library Recommendations

### **Reusable Components to Create**

**1. KPICard.tsx**
```typescript
interface KPICardProps {
  title: string;
  value: number | null;
  unit?: string;
  trend?: 'up' | 'down' | 'neutral';
}

const KPICard = ({ title, value, unit = '%', trend }: KPICardProps) => (
  <div className="bg-white rounded-lg shadow p-6">
    <h3 className="text-sm font-medium text-secondary-600">{title}</h3>
    <p className="text-3xl font-bold text-secondary-900 mt-2">
      {value?.toFixed(1)}{unit}
    </p>
  </div>
);
```

**2. DataTable.tsx**
Generic table component with sorting, pagination, filters.

**3. Modal.tsx**
Using `@headlessui/react Dialog`:
```typescript
import { Dialog } from '@headlessui/react';

const Modal = ({ isOpen, onClose, title, children }) => (
  <Dialog open={isOpen} onClose={onClose} className="relative z-50">
    <div className="fixed inset-0 bg-black/30" aria-hidden="true" />
    <div className="fixed inset-0 flex items-center justify-center p-4">
      <Dialog.Panel className="bg-white rounded-lg p-6 max-w-md w-full">
        <Dialog.Title className="text-lg font-semibold">{title}</Dialog.Title>
        {children}
      </Dialog.Panel>
    </div>
  </Dialog>
);
```

**4. Badge.tsx**
For status indicators:
```typescript
const Badge = ({ status, label }) => {
  const colors = {
    success: 'bg-success-100 text-success-800',
    warning: 'bg-warning-100 text-warning-800',
    danger: 'bg-danger-100 text-danger-800',
  };

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[status]}`}>
      {label}
    </span>
  );
};
```

---

## 🔗 API Service Extensions

Add to `src/services/api.ts`:

```typescript
// Efficiency
export const getEmployeeEfficiency = (employeeId: number, start: string, end: string) =>
  api.get(`/efficiency/${employeeId}?start=${start}&end=${end}`);

// Dashboard
export const getDashboardSummary = (teamId?: string) =>
  api.get(`/reporting/dashboard/summary${teamId ? `?team_id=${teamId}` : ''}`);

// Validations
export const getValidations = (resolved: boolean = false) =>
  api.get(`/supervisor/validations?resolved=${resolved}`);

export const resolveValidation = (id: number, note: string) =>
  api.patch(`/supervisor/validations/${id}/resolve`, { resolution_note: note });

// Reports
export const getMonthlyReport = (month: string) =>
  api.get(`/reporting/report/monthly?month=${month}`);

// Activity Codes
export const getActivityCodes = () => api.get('/activity-codes');
export const createActivityCode = (data: any) => api.post('/activity-codes', data);
export const updateActivityCode = (id: number, data: any) => api.patch(`/activity-codes/${id}`, data);
export const deleteActivityCode = (id: number) => api.delete(`/activity-codes/${id}`);
```

---

## 🎨 Tailwind Utility Classes Reference

```css
/* Backgrounds */
bg-primary-500  /* Main blue-grey */
bg-secondary-50 /* Light grey background */
bg-accent-400   /* Teal accent */

/* Text */
text-secondary-900  /* Dark text */
text-secondary-600  /* Muted text */
text-primary-600    /* Primary text */

/* Buttons */
bg-primary-600 hover:bg-primary-700 text-white  /* Primary button */
bg-secondary-200 hover:bg-secondary-300         /* Secondary button */
bg-danger-600 hover:bg-danger-700 text-white    /* Danger button */

/* Cards */
bg-white rounded-lg shadow p-6

/* Forms */
border border-secondary-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-primary-500
```

---

## 🚀 Quick Start Commands

```bash
# Install dependencies
cd frontend
npm install

# Create .env
copy .env.example .env

# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run tests
npm run test

# Lint
npm run lint
```

---

## ✅ Checklist

### **Phase 1** ✅
- [x] JWT decoding & role extraction
- [x] Enhanced authService
- [x] ProtectedRoute component
- [x] useRole hook
- [x] Sidebar & Header components
- [x] Role-based layouts

### **Phase 2** ⏳
- [ ] Operator Dashboard
- [ ] JobCard Form with validation
- [ ] JobCard List

### **Phase 3** ⏳
- [ ] Supervisor Dashboard
- [ ] Assignment Panel
- [ ] Validation Panel
- [ ] Reports Page

### **Phase 4** ⏳
- [ ] Activity Codes CRUD
- [ ] Machines CRUD
- [ ] Employees Management

### **Phase 5** ⏳
- [ ] Charts with recharts
- [ ] Analytics dashboards

### **Phase 6** ⏳
- [ ] Update App.tsx routing
- [ ] Add toast notifications

### **Phase 7** ⏳
- [ ] Dockerfile
- [ ] nginx config
- [ ] docker-compose

### **Phase 8** ⏳
- [ ] Vitest setup
- [ ] Component tests
- [ ] Integration tests

---

## 📖 Next Steps

1. **Run `npm install`** to install all dependencies (errors will disappear!)
2. **Create `.env`** file from `.env.example`
3. **Update `App.tsx`** with new routing (see Phase 6)
4. **Start implementing operator pages** (highest priority)
5. **Test with backend** running at `http://localhost:8000`

---

## 🆘 Need Help?

**TypeScript Errors?**
- Run `npm install` - all errors are due to missing packages

**API Not Working?**
- Ensure backend is running at `http://localhost:8000`
- Check `.env` has correct `VITE_API_URL`
- Check CORS is configured in backend

**Routing Issues?**
- Verify role-based redirects in `authService.getRoleHomeRoute()`
- Check `ProtectedRoute` allowedRoles prop

---

Your frontend foundation is **complete**! 🎉

**Ready to build the remaining pages following the patterns established.**
