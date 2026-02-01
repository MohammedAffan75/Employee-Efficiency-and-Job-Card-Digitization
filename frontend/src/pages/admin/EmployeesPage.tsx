import { useEffect, useState } from 'react';
import api from '../../services/api';
import toast from 'react-hot-toast';
import { Employee, RoleEnum, EfficiencyTypeEnum } from '../../types';
import { Users, Search, UserCheck, UserX, Shield, Plus, Trash2 } from 'lucide-react';
import { useRole } from '../../hooks/useRole';

const EmployeesPage = () => {
  const { isSupervisor, isAdmin } = useRole();
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterRole, setFilterRole] = useState<string>('');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [createForm, setCreateForm] = useState({
    ec_number: '',
    name: '',
    role: RoleEnum.OPERATOR,
    join_date: new Date().toISOString().split('T')[0],
    password: '',
    supervisor_efficiency_module: '' as '' | EfficiencyTypeEnum,
  });
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    fetchEmployees();
  }, []);

  const fetchEmployees = async () => {
    setLoading(true);
    try {
      const response = await api.get('/employees');
      setEmployees(response.data);
    } catch (error) {
      console.error('Failed to fetch employees:', error);
      toast.error('Failed to load employees');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteEmployee = async (employee: Employee) => {
    if (!window.confirm(`Delete ${employee.name} (${employee.ec_number})? This cannot be undone.`)) {
      return;
    }

    try {
      await api.delete(`/employees/${employee.id}`);
      toast.success('Employee deleted successfully');
      fetchEmployees();
    } catch (error: any) {
      console.error('Failed to delete employee:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete employee');
    }
  };

  const toggleActiveStatus = async (employee: Employee) => {
    try {
      await api.patch(`/employees/${employee.id}`, {
        is_active: !employee.is_active,
      });
      toast.success(
        `Employee ${employee.is_active ? 'deactivated' : 'activated'} successfully`
      );
      fetchEmployees();
    } catch (error: any) {
      console.error('Failed to update employee:', error);
      toast.error(error.response?.data?.detail || 'Failed to update employee');
    }
  };

  const resetCreateForm = () => {
    setCreateForm({
      ec_number: '',
      name: '',
      role: RoleEnum.OPERATOR,
      join_date: new Date().toISOString().split('T')[0],
      password: '',
      supervisor_efficiency_module: '',
    });
    setFormError(null);
  };

  const handleCreateEmployee = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFormError(null);

    const { ec_number, name, role, join_date, password, supervisor_efficiency_module } = createForm;
    if (!ec_number.trim() || !name.trim() || !password.trim()) {
      setFormError('Please fill in all required fields.');
      return;
    }
    if (role === RoleEnum.SUPERVISOR && !supervisor_efficiency_module) {
      setFormError('Supervisor efficiency module is required.');
      return;
    }

    setCreateLoading(true);
    try {
      await api.post('/employees', {
        ec_number: ec_number.trim(),
        name: name.trim(),
        role,
        join_date,
        password,
        supervisor_efficiency_module:
          role === RoleEnum.SUPERVISOR ? supervisor_efficiency_module : null,
      });
      toast.success('Employee created successfully');
      setIsCreateModalOpen(false);
      resetCreateForm();
      fetchEmployees();
    } catch (error: any) {
      console.error('Failed to create employee:', error);
      toast.error(error.response?.data?.detail || 'Failed to create employee');
    } finally {
      setCreateLoading(false);
    }
  };

  const handleCreateFieldChange = (field: string, value: string) => {
    setCreateForm((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const getRoleBadge = (role: RoleEnum) => {
    const colors: Record<string, string> = {
      OPERATOR: 'bg-primary-100 text-primary-800',
      SUPERVISOR: 'bg-accent-100 text-accent-800',
      ADMIN: 'bg-danger-100 text-danger-800',
    };

    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${colors[role]}`}>
        {role}
      </span>
    );
  };

  // Filter employees
  const filteredEmployees = employees.filter((emp) => {
    const matchesSearch =
      emp.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      emp.ec_number.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesRole = !filterRole || emp.role === filterRole;
    return matchesSearch && matchesRole;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-secondary-900">Employees</h1>
        <p className="text-secondary-600 mt-1">Manage employee accounts and permissions</p>
        {(isSupervisor || isAdmin) && (
          <button
            onClick={() => {
              resetCreateForm();
              setIsCreateModalOpen(true);
            }}
            className="mt-4 inline-flex items-center space-x-2 rounded-md bg-primary-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
          >
            <Plus className="w-4 h-4" />
            <span>Add Employee</span>
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-secondary-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by name or EC number..."
              className="w-full pl-10 pr-3 py-2 border border-secondary-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          {/* Role Filter - Only show for admins */}
          {!isSupervisor && (
            <div>
              <select
                value={filterRole}
                onChange={(e) => setFilterRole(e.target.value)}
                className="w-full px-3 py-2 border border-secondary-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">All Roles</option>
                <option value={RoleEnum.OPERATOR}>Operator</option>
                <option value={RoleEnum.SUPERVISOR}>Supervisor</option>
                <option value={RoleEnum.ADMIN}>Admin</option>
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow-md p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-secondary-600">
                {isSupervisor ? 'Your Operators' : 'Total Employees'}
              </p>
              <p className="text-2xl font-bold text-secondary-900">{employees.length}</p>
            </div>
            <Users className="w-8 h-8 text-primary-600" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-secondary-600">Active</p>
              <p className="text-2xl font-bold text-success-600">
                {employees.filter((e) => e.is_active).length}
              </p>
            </div>
            <UserCheck className="w-8 h-8 text-success-600" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-secondary-600">Inactive</p>
              <p className="text-2xl font-bold text-danger-600">
                {employees.filter((e) => !e.is_active).length}
              </p>
            </div>
            <UserX className="w-8 h-8 text-danger-600" />
          </div>
        </div>
        {!isSupervisor && (
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-secondary-600">Admins</p>
                <p className="text-2xl font-bold text-warning-600">
                  {employees.filter((e) => e.role === RoleEnum.ADMIN).length}
                </p>
              </div>
              <Shield className="w-8 h-8 text-warning-600" />
            </div>
          </div>
        )}
      </div>

      {/* Employees Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          </div>
        ) : filteredEmployees.length === 0 ? (
          <div className="text-center py-12 text-secondary-500">
            <Users className="w-16 h-16 mx-auto mb-4 text-secondary-400" />
            <p className="text-lg font-medium">No employees found</p>
            <p className="text-sm mt-2">Try adjusting your filters</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-secondary-200">
                <thead className="bg-secondary-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                      Employee
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                      EC Number
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                      Role
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                      Join Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-secondary-700 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-secondary-200">
                  {filteredEmployees.map((employee) => (
                    <tr key={employee.id} className="hover:bg-secondary-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-10 w-10 bg-primary-100 rounded-full flex items-center justify-center">
                            <span className="text-primary-700 font-medium">
                              {employee.name.charAt(0)}
                            </span>
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-secondary-900">
                              {employee.name}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary-900">
                        {employee.ec_number}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {getRoleBadge(employee.role)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary-600">
                        {new Date(employee.join_date).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {employee.is_active ? (
                          <span className="flex items-center space-x-1 text-success-600">
                            <UserCheck className="w-4 h-4" />
                            <span>Active</span>
                          </span>
                        ) : (
                          <span className="flex items-center space-x-1 text-danger-600">
                            <UserX className="w-4 h-4" />
                            <span>Inactive</span>
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => toggleActiveStatus(employee)}
                            className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                              employee.is_active
                                ? 'bg-danger-100 text-danger-800 hover:bg-danger-200'
                                : 'bg-success-100 text-success-800 hover:bg-success-200'
                            }`}
                          >
                            {employee.is_active ? 'Deactivate' : 'Activate'}
                          </button>
                          {((isSupervisor && employee.role === RoleEnum.OPERATOR) ||
                            (isAdmin && employee.role === RoleEnum.SUPERVISOR)) && (
                            <button
                              onClick={() => handleDeleteEmployee(employee)}
                              className="inline-flex items-center gap-1 px-3 py-1 text-xs font-medium rounded-md bg-danger-600 text-white hover:bg-danger-700"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                              Delete
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Footer */}
            <div className="bg-secondary-50 px-6 py-4 border-t border-secondary-200">
              <p className="text-sm text-secondary-700">
                Showing <strong>{filteredEmployees.length}</strong> of <strong>{employees.length}</strong> employees
              </p>
            </div>
          </>
        )}
      </div>

      {/* Create Employee Modal */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40 px-4">
          <div className="w-full max-w-lg rounded-lg bg-white shadow-xl">
            <div className="border-b border-secondary-200 px-6 py-4">
              <h2 className="text-xl font-semibold text-secondary-900">Add New Employee</h2>
              <p className="mt-1 text-sm text-secondary-600">Create a new employee account with role and team assignment.</p>
            </div>
            <form onSubmit={handleCreateEmployee} className="px-6 py-4 space-y-4">
              {formError && (
                <div className="rounded-md border border-danger-200 bg-danger-50 px-3 py-2 text-sm text-danger-700">
                  {formError}
                </div>
              )}

              <div>
                <label htmlFor="ec_number" className="block text-sm font-medium text-secondary-700">
                  EC Number
                </label>
                <input
                  id="ec_number"
                  type="text"
                  value={createForm.ec_number}
                  onChange={(e) => handleCreateFieldChange('ec_number', e.target.value.toUpperCase())}
                  className="mt-1 w-full rounded-md border border-secondary-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="e.g., OP002"
                  required
                />
              </div>

              <div>
                <label htmlFor="name" className="block text-sm font-medium text-secondary-700">
                  Full Name
                </label>
                <input
                  id="name"
                  type="text"
                  value={createForm.name}
                  onChange={(e) => handleCreateFieldChange('name', e.target.value)}
                  className="mt-1 w-full rounded-md border border-secondary-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="Employee name"
                  required
                />
              </div>

              <div>
                <label htmlFor="role" className="block text-sm font-medium text-secondary-700">
                  Role
                </label>
                <select
                  id="role"
                  value={createForm.role}
                  onChange={(e) => handleCreateFieldChange('role', e.target.value as RoleEnum)}
                  className="mt-1 w-full rounded-md border border-secondary-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  disabled={isSupervisor}  // Supervisors can only create operators
                >
                  <option value={RoleEnum.OPERATOR}>Operator</option>
                  {isAdmin && (
                    <>
                      <option value={RoleEnum.SUPERVISOR}>Supervisor</option>
                      <option value={RoleEnum.ADMIN}>Admin</option>
                    </>
                  )}
                </select>
                {isSupervisor && (
                  <p className="mt-1 text-xs text-secondary-500">
                    Supervisors can only create operator accounts
                  </p>
                )}
              </div>

              {createForm.role === RoleEnum.SUPERVISOR && !isSupervisor && (
                <div>
                  <label htmlFor="supervisor_efficiency_module" className="block text-sm font-medium text-secondary-700">
                    Supervisor Module
                  </label>
                  <select
                    id="supervisor_efficiency_module"
                    value={createForm.supervisor_efficiency_module}
                    onChange={(e) => handleCreateFieldChange('supervisor_efficiency_module', e.target.value)}
                    className="mt-1 w-full rounded-md border border-secondary-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
                    required
                  >
                    <option value="">Select module</option>
                    <option value={EfficiencyTypeEnum.TIME_BASED}>Time Based</option>
                    <option value={EfficiencyTypeEnum.QUANTITY_BASED}>Quantity Based</option>
                    <option value={EfficiencyTypeEnum.TASK_BASED}>Task Based</option>
                  </select>
                </div>
              )}

              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <label htmlFor="join_date" className="block text-sm font-medium text-secondary-700">
                    Join Date
                  </label>
                  <input
                    id="join_date"
                    type="date"
                    value={createForm.join_date}
                    max={new Date().toISOString().split('T')[0]}
                    onChange={(e) => handleCreateFieldChange('join_date', e.target.value)}
                    className="mt-1 w-full rounded-md border border-secondary-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
                    required
                  />
                </div>

                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-secondary-700">
                    Temporary Password
                  </label>
                  <input
                    id="password"
                    type="password"
                    value={createForm.password}
                    onChange={(e) => handleCreateFieldChange('password', e.target.value)}
                    className="mt-1 w-full rounded-md border border-secondary-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
                    placeholder="Set initial password"
                    required
                    minLength={6}
                  />
                </div>
              </div>

              <div className="flex items-center justify-end space-x-3 border-t border-secondary-200 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setIsCreateModalOpen(false);
                    resetCreateForm();
                  }}
                  className="rounded-md border border-secondary-300 px-4 py-2 text-sm font-medium text-secondary-700 hover:bg-secondary-100"
                  disabled={createLoading}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="inline-flex items-center rounded-md bg-primary-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-70"
                  disabled={createLoading}
                >
                  {createLoading ? 'Creating...' : 'Create Employee'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default EmployeesPage;
