import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

// Auth Pages
import Login from './pages/Login';

// Layouts
import OperatorLayout from './layouts/OperatorLayout';
import SupervisorLayout from './layouts/SupervisorLayout';
import AdminLayout from './layouts/AdminLayout';

// Operator Pages
import OperatorDashboard from './pages/operator/OperatorDashboard';
import JobCardForm from './pages/operator/JobCardForm';
import JobCardList from './pages/operator/JobCardList';
import AssignedTasks from './pages/operator/AssignedTasks';
import OperatorAnalytics from './pages/operator/AnalyticsPage';

// Supervisor Pages
import SupervisorDashboard from './pages/supervisor/SupervisorDashboard';
import AssignmentPanel from './pages/supervisor/AssignmentPanel';
import ValidationPanel from './pages/supervisor/ValidationPanel';
import TeamAnalytics from './pages/supervisor/TeamAnalytics';
import ReportsPage from './pages/supervisor/ReportsPage';

// Admin Pages
import AdminDashboard from './pages/admin/AdminDashboard';
import ActivityCodesPage from './pages/admin/ActivityCodesPage';
import MachinesPage from './pages/admin/MachinesPage';
import WorkOrdersPage from './pages/admin/WorkOrdersPage';
import EmployeesPage from './pages/admin/EmployeesPage';

import { RoleEnum } from './types';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Toaster position="top-right" />
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<Navigate to="/login" replace />} />

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
            <Route path="assigned" element={<AssignedTasks />} />
            <Route path="jobcards/new" element={<JobCardForm />} />
            <Route path="jobcards/:id/edit" element={<JobCardForm />} />
            <Route path="analytics" element={<OperatorAnalytics />} />
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
            <Route path="analytics" element={<TeamAnalytics />} />
            <Route path="reports" element={<ReportsPage />} />
            <Route path="employees" element={<EmployeesPage />} />
            <Route path="activity-codes" element={<ActivityCodesPage />} />
            <Route path="machines" element={<MachinesPage />} />
            <Route path="work-orders" element={<WorkOrdersPage />} />
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
            <Route index element={<AdminDashboard />} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
