import { useEffect, useState, Fragment } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Dialog, Transition } from '@headlessui/react';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import toast from 'react-hot-toast';
import { Employee, WorkOrder, ActivityCode } from '../../types';
import { Users, Send, CheckCircle, X } from 'lucide-react';

const assignmentSchema = z.object({
  work_order_id: z.number({ required_error: 'Work order is required' }),
  activity_code_id: z.number({ required_error: 'Activity code is required' }),
  employee_ids: z.array(z.number()).min(1, 'Select at least one operator'),
  mode: z.enum(['MANUAL', 'AUTO_SPLIT']),
  manual_hours: z.number().positive().optional(),
});

type AssignmentFormData = z.infer<typeof assignmentSchema>;

const AssignmentPanel = () => {
  const { user } = useAuth();
  const supervisorModule = user?.supervisor_efficiency_module || '';
  const [operators, setOperators] = useState<Employee[]>([]);
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([]);
  const [activityCodes, setActivityCodes] = useState<ActivityCode[]>([]);
  const [loading, setLoading] = useState(false);
  const [confirmModalOpen, setConfirmModalOpen] = useState(false);
  const [pendingAssignment, setPendingAssignment] = useState<AssignmentFormData | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors },
  } = useForm<AssignmentFormData>({
    resolver: zodResolver(assignmentSchema),
    defaultValues: {
      mode: 'AUTO_SPLIT',
      employee_ids: [],
    },
  });

  const mode = watch('mode');
  const selectedEmployees = watch('employee_ids');

  useEffect(() => {
    fetchFormData();
  }, [user]);

  const fetchFormData = async () => {
    try {
      const [operatorsRes, workOrdersRes, activityCodesRes] = await Promise.all([
        api.get(`/employees?role=OPERATOR`),
        api.get('/work-orders'),
        api.get('/activity-codes'),
      ]);

      // Safety: ensure only operators are shown, even if backend returns other roles
      const allEmployees: Employee[] = operatorsRes.data;
      const onlyOperators = allEmployees.filter((emp) => emp.role === 'OPERATOR');
      setOperators(onlyOperators);
      setWorkOrders(workOrdersRes.data);
      const allCodes: ActivityCode[] = activityCodesRes.data;
      setActivityCodes(
        supervisorModule
          ? allCodes.filter((ac) => ac.efficiency_type === supervisorModule)
          : allCodes
      );
    } catch (error) {
      console.error('Failed to fetch form data:', error);
      toast.error('Failed to load form data');
    }
  };

  const handleEmployeeToggle = (employeeId: number) => {
    const current = selectedEmployees || [];
    if (current.includes(employeeId)) {
      setValue(
        'employee_ids',
        current.filter((id) => id !== employeeId)
      );
    } else {
      setValue('employee_ids', [...current, employeeId]);
    }
  };

  const onSubmit = (data: AssignmentFormData) => {
    setPendingAssignment(data);
    setConfirmModalOpen(true);
  };

  const confirmAssignment = async () => {
    if (!pendingAssignment) return;

    setLoading(true);
    setConfirmModalOpen(false);

    try {
      // Find the selected work order to get planned_qty
      const selectedWO = workOrders.find(wo => wo.id === pendingAssignment.work_order_id);
      const plannedQty = selectedWO?.planned_qty || 0;
      
      // Determine hours per employee based on mode
      const hoursPerEmployee = pendingAssignment.mode === 'MANUAL' 
        ? (pendingAssignment.manual_hours || 8)
        : 8; // Default 8 hours for auto-split
      
      // Calculate qty per employee (split equally)
      const qtyPerEmployee = plannedQty / pendingAssignment.employee_ids.length;
      
      // Convert employee_ids to assignments array
      const assignments = pendingAssignment.employee_ids.map(employee_id => ({
        employee_id,
        hours: hoursPerEmployee,
        qty: qtyPerEmployee,
      }));
      
      // Convert mode to backend format (lowercase with underscore)
      const backendMode = pendingAssignment.mode === 'MANUAL' ? 'manual' : 'auto_split_hours';
      
      const payload = {
        work_order_id: pendingAssignment.work_order_id,
        activity_code_id: pendingAssignment.activity_code_id,
        assignments,
        mode: backendMode,
        entry_date: new Date().toISOString().split('T')[0], // YYYY-MM-DD
        status: 'C', // Complete
      };

      await api.post('/supervisor/assign', payload);
      toast.success('Work assigned successfully!');
      reset();
      setValue('employee_ids', []);
      setPendingAssignment(null);
    } catch (error: any) {
      console.error('Failed to assign work:', error);
      toast.error(error.response?.data?.detail || 'Failed to assign work');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-secondary-900">Assignment Panel</h1>
        <p className="text-secondary-600 mt-1">Assign work to operators</p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Work Assignment Details */}
        <div className="bg-white rounded-lg shadow-md p-6 space-y-4">
          <h2 className="text-lg font-semibold text-secondary-900 mb-4">Work Details</h2>

          {/* Work Order */}
          <div>
            <label htmlFor="work_order_id" className="block text-sm font-medium text-secondary-700 mb-1">
              Work Order <span className="text-danger-600">*</span>
            </label>
            <select
              id="work_order_id"
              {...register('work_order_id', { valueAsNumber: true })}
              className="w-full px-3 py-2 border border-secondary-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="">Select Work Order</option>
              {workOrders.map((wo) => (
                <option key={wo.id} value={wo.id}>
                  {wo.wo_number} - Qty: {wo.planned_qty} - MSD: {wo.msd_month}
                </option>
              ))}
            </select>
            {errors.work_order_id && (
              <p className="mt-1 text-sm text-danger-600">{errors.work_order_id.message}</p>
            )}
          </div>

          {/* Activity Code */}
          <div>
            <label
              htmlFor="activity_code_id"
              className="block text-sm font-medium text-secondary-700 mb-1"
            >
              Activity Code <span className="text-danger-600">*</span>
            </label>
            <select
              id="activity_code_id"
              {...register('activity_code_id', { valueAsNumber: true })}
              className="w-full px-3 py-2 border border-secondary-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="">Select Activity Code</option>
              {activityCodes.map((ac) => (
                <option key={ac.id} value={ac.id}>
                  {ac.code} - {ac.description}
                </option>
              ))}
            </select>
            {errors.activity_code_id && (
              <p className="mt-1 text-sm text-danger-600">{errors.activity_code_id.message}</p>
            )}
          </div>

          {/* Assignment Mode */}
          <div>
            <label className="block text-sm font-medium text-secondary-700 mb-2">
              Assignment Mode <span className="text-danger-600">*</span>
            </label>
            <div className="flex items-center space-x-6">
              <label className="flex items-center">
                <input
                  type="radio"
                  value="AUTO_SPLIT"
                  {...register('mode')}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-secondary-300"
                />
                <span className="ml-2 text-sm text-secondary-700">Auto-Split Hours</span>
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  value="MANUAL"
                  {...register('mode')}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-secondary-300"
                />
                <span className="ml-2 text-sm text-secondary-700">Manual Hours Entry</span>
              </label>
            </div>
          </div>

          {/* Manual Hours Input */}
          {mode === 'MANUAL' && (
            <div>
              <label htmlFor="manual_hours" className="block text-sm font-medium text-secondary-700 mb-1">
                Hours per Operator <span className="text-danger-600">*</span>
              </label>
              <input
                type="number"
                id="manual_hours"
                step="0.01"
                {...register('manual_hours', { valueAsNumber: true })}
                className="w-full px-3 py-2 border border-secondary-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                placeholder="Enter hours"
              />
              {errors.manual_hours && (
                <p className="mt-1 text-sm text-danger-600">{errors.manual_hours.message}</p>
              )}
            </div>
          )}
        </div>

        {/* Operator Selection */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-secondary-900">
              Select Operators ({selectedEmployees?.length || 0} selected)
            </h2>
            {selectedEmployees && selectedEmployees.length > 0 && (
              <button
                type="button"
                onClick={() => setValue('employee_ids', [])}
                className="text-sm text-danger-600 hover:text-danger-700"
              >
                Clear All
              </button>
            )}
          </div>

          {operators.length === 0 ? (
            <div className="text-center py-8 text-secondary-500">
              <Users className="w-12 h-12 mx-auto mb-2 text-secondary-400" />
              <p>No operators found in your team</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {operators.map((operator) => {
                const isSelected = selectedEmployees?.includes(operator.id);
                return (
                  <button
                    key={operator.id}
                    type="button"
                    onClick={() => handleEmployeeToggle(operator.id)}
                    className={`p-4 border-2 rounded-lg transition-all text-left ${
                      isSelected
                        ? 'border-primary-600 bg-primary-50'
                        : 'border-secondary-200 hover:border-secondary-300'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-secondary-900">{operator.name}</p>
                        <p className="text-sm text-secondary-600">{operator.ec_number}</p>
                      </div>
                      {isSelected && <CheckCircle className="w-5 h-5 text-primary-600" />}
                    </div>
                  </button>
                );
              })}
            </div>
          )}

          {errors.employee_ids && (
            <p className="mt-2 text-sm text-danger-600">{errors.employee_ids.message}</p>
          )}
        </div>

        {/* Submit Button */}
        <div className="flex items-center justify-end space-x-3">
          <button
            type="button"
            onClick={() => reset()}
            className="px-4 py-2 border border-secondary-300 text-secondary-700 rounded-md hover:bg-secondary-50 transition-colors"
          >
            Reset Form
          </button>
          <button
            type="submit"
            disabled={loading}
            className="flex items-center space-x-2 px-6 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-4 h-4" />
            <span>{loading ? 'Assigning...' : 'Assign Work'}</span>
          </button>
        </div>
      </form>

      {/* Confirmation Modal */}
      <Transition appear show={confirmModalOpen} as={Fragment}>
        <Dialog
          as="div"
          className="relative z-50"
          onClose={() => setConfirmModalOpen(false)}
        >
          <Transition.Child
            as={Fragment}
            enter="ease-out duration-300"
            enterFrom="opacity-0"
            enterTo="opacity-100"
            leave="ease-in duration-200"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <div className="fixed inset-0 bg-black bg-opacity-25" />
          </Transition.Child>

          <div className="fixed inset-0 overflow-y-auto">
            <div className="flex min-h-full items-center justify-center p-4">
              <Transition.Child
                as={Fragment}
                enter="ease-out duration-300"
                enterFrom="opacity-0 scale-95"
                enterTo="opacity-100 scale-100"
                leave="ease-in duration-200"
                leaveFrom="opacity-100 scale-100"
                leaveTo="opacity-0 scale-95"
              >
                <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-lg bg-white p-6 shadow-xl transition-all">
                  <div className="flex items-center justify-between mb-4">
                    <Dialog.Title className="text-lg font-semibold text-secondary-900">
                      Confirm Assignment
                    </Dialog.Title>
                    <button
                      onClick={() => setConfirmModalOpen(false)}
                      className="text-secondary-400 hover:text-secondary-600"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>

                  <div className="space-y-3 mb-6">
                    <p className="text-sm text-secondary-700">
                      You are about to assign work to{' '}
                      <strong>{pendingAssignment?.employee_ids.length}</strong> operator(s).
                    </p>
                    <p className="text-sm text-secondary-700">
                      Mode: <strong>{pendingAssignment?.mode === 'AUTO_SPLIT' ? 'Auto-Split Hours' : 'Manual Entry'}</strong>
                    </p>
                    {pendingAssignment?.mode === 'MANUAL' && (
                      <p className="text-sm text-secondary-700">
                        Hours per Operator: <strong>{pendingAssignment?.manual_hours}</strong>
                      </p>
                    )}
                  </div>

                  <div className="flex items-center justify-end space-x-3">
                    <button
                      type="button"
                      onClick={() => setConfirmModalOpen(false)}
                      className="px-4 py-2 border border-secondary-300 text-secondary-700 rounded-md hover:bg-secondary-50 transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={confirmAssignment}
                      className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors"
                    >
                      Confirm Assignment
                    </button>
                  </div>
                </Dialog.Panel>
              </Transition.Child>
            </div>
          </div>
        </Dialog>
      </Transition>
    </div>
  );
};

export default AssignmentPanel;
