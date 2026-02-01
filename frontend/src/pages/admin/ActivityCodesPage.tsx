import { useEffect, useState, Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import api from '../../services/api';
import toast from 'react-hot-toast';
import { ActivityCode, EfficiencyTypeEnum } from '../../types';
import { Plus, Edit, Trash2, X, Save, Database } from 'lucide-react';
import { useRole } from '../../hooks/useRole';
import { useAuth } from '../../context/AuthContext';

const activityCodeSchema = z.object({
  code: z.string().min(1, 'Code is required'),
  description: z.string().min(1, 'Description is required'),
  efficiency_type: z.nativeEnum(EfficiencyTypeEnum),
  std_hours_per_unit: z.number().positive().optional().nullable(),
  std_qty_per_hour: z.number().positive().optional().nullable(),
});

type ActivityCodeFormData = z.infer<typeof activityCodeSchema>;

const ActivityCodesPage = () => {
  const { isSupervisor } = useRole();
  const { user } = useAuth();
  const [activityCodes, setActivityCodes] = useState<ActivityCode[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [editingCode, setEditingCode] = useState<ActivityCode | null>(null);
  const [deletingCode, setDeletingCode] = useState<ActivityCode | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors },
  } = useForm<ActivityCodeFormData>({
    resolver: zodResolver(activityCodeSchema),
  });

  const efficiencyType = watch('efficiency_type');
  const supervisorModule = user?.supervisor_efficiency_module as EfficiencyTypeEnum | undefined;

  useEffect(() => {
    fetchActivityCodes();
  }, [user]);

  const fetchActivityCodes = async () => {
    setLoading(true);
    try {
      const response = await api.get('/activity-codes');
      const allCodes: ActivityCode[] = response.data;

      // For supervisors, restrict to their assigned efficiency module
      if (isSupervisor && user?.supervisor_efficiency_module) {
        const supervisorModule = user.supervisor_efficiency_module as EfficiencyTypeEnum | string;
        setActivityCodes(allCodes.filter((code) => code.efficiency_type === supervisorModule));
      } else {
        setActivityCodes(allCodes);
      }
    } catch (error) {
      console.error('Failed to fetch activity codes:', error);
      toast.error('Failed to load activity codes');
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = () => {
    setEditingCode(null);
    reset({
      code: '',
      description: '',
      efficiency_type: isSupervisor && supervisorModule ? supervisorModule : EfficiencyTypeEnum.QUANTITY_BASED,
      std_hours_per_unit: null,
      std_qty_per_hour: null,
    });
    setModalOpen(true);
  };

  const handleEdit = (code: ActivityCode) => {
    setEditingCode(code);
    reset({
      code: code.code,
      description: code.description,
      efficiency_type: isSupervisor && supervisorModule ? supervisorModule : code.efficiency_type,
      std_hours_per_unit: code.std_hours_per_unit,
      std_qty_per_hour: code.std_qty_per_hour,
    });
    setModalOpen(true);
  };

  const handleDeleteClick = (code: ActivityCode) => {
    setDeletingCode(code);
    setDeleteModalOpen(true);
  };

  const onSubmit = async (data: ActivityCodeFormData) => {
    setSubmitting(true);
    try {
      if (editingCode) {
        await api.patch(`/activity-codes/${editingCode.id}`, data);
        toast.success('Activity code updated successfully');
      } else {
        await api.post('/activity-codes', data);
        toast.success('Activity code created successfully');
      }
      setModalOpen(false);
      fetchActivityCodes();
    } catch (error: any) {
      console.error('Failed to save activity code:', error);
      toast.error(error.response?.data?.detail || 'Failed to save activity code');
    } finally {
      setSubmitting(false);
    }
  };

  const confirmDelete = async () => {
    if (!deletingCode) return;

    setSubmitting(true);
    try {
      await api.delete(`/activity-codes/${deletingCode.id}`);
      toast.success('Activity code deleted successfully');
      setDeleteModalOpen(false);
      setDeletingCode(null);
      fetchActivityCodes();
    } catch (error: any) {
      console.error('Failed to delete activity code:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete activity code');
    } finally {
      setSubmitting(false);
    }
  };

  const getEfficiencyBadge = (type: EfficiencyTypeEnum) => {
    const colors: Record<string, string> = {
      TIME_BASED: 'bg-primary-100 text-primary-800',
      QUANTITY_BASED: 'bg-accent-100 text-accent-800',
      TASK_BASED: 'bg-warning-100 text-warning-800',
    };

    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${colors[type]}`}>
        {type.replace(/_/g, ' ')}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-secondary-900">Activity Codes</h1>
          <p className="text-secondary-600 mt-1">Manage activity code master data</p>
        </div>
        {isSupervisor && (
          <button
            onClick={handleAdd}
            className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors"
          >
            <Plus className="w-5 h-5" />
            <span>Add Activity Code</span>
          </button>
        )}
      </div>

      {/* Activity Codes Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          </div>
        ) : activityCodes.length === 0 ? (
          <div className="text-center py-12 text-secondary-500">
            <Database className="w-16 h-16 mx-auto mb-4 text-secondary-400" />
            <p className="text-lg font-medium">No activity codes found</p>
            <p className="text-sm mt-2">Click "Add Activity Code" to create one</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-secondary-200">
              <thead className="bg-secondary-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                    Code
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                    Description
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                    Efficiency Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                    Expected Hours
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                    Expected Quantity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                    Last Updated
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-secondary-700 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-secondary-200">
                {activityCodes.map((code) => (
                  <tr key={code.id} className="hover:bg-secondary-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-secondary-900">
                      {code.code}
                    </td>
                    <td className="px-6 py-4 text-sm text-secondary-900">{code.description}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {getEfficiencyBadge(code.efficiency_type)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary-900">
                      {code.std_hours_per_unit || '—'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary-900">
                      {code.std_qty_per_hour || '—'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary-600">
                      {new Date(code.last_updated).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={() => handleEdit(code)}
                          className="p-1 text-primary-600 hover:text-primary-700"
                          title="Edit"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteClick(code)}
                          className="p-1 text-danger-600 hover:text-danger-700"
                          title="Delete"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add/Edit Modal */}
      <Transition appear show={modalOpen} as={Fragment}>
        <Dialog as="div" className="relative z-50" onClose={() => setModalOpen(false)}>
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
                      {editingCode ? 'Edit Activity Code' : 'Add Activity Code'}
                    </Dialog.Title>
                    <button
                      onClick={() => setModalOpen(false)}
                      className="text-secondary-400 hover:text-secondary-600"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>

                  <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    {/* Code */}
                    <div>
                      <label htmlFor="code" className="block text-sm font-medium text-secondary-700 mb-1">
                        Code <span className="text-danger-600">*</span>
                      </label>
                      <input
                        type="text"
                        id="code"
                        {...register('code')}
                        className="w-full px-3 py-2 border border-secondary-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        placeholder="e.g., AC001"
                      />
                      {errors.code && <p className="mt-1 text-sm text-danger-600">{errors.code.message}</p>}
                    </div>

                    {/* Description */}
                    <div>
                      <label htmlFor="description" className="block text-sm font-medium text-secondary-700 mb-1">
                        Description <span className="text-danger-600">*</span>
                      </label>
                      <input
                        type="text"
                        id="description"
                        {...register('description')}
                        className="w-full px-3 py-2 border border-secondary-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        placeholder="e.g., Assembly Work"
                      />
                      {errors.description && (
                        <p className="mt-1 text-sm text-danger-600">{errors.description.message}</p>
                      )}
                    </div>

                    {/* Efficiency Type */}
                    <div>
                      <label htmlFor="efficiency_type" className="block text-sm font-medium text-secondary-700 mb-1">
                        Efficiency Type <span className="text-danger-600">*</span>
                      </label>
                      {isSupervisor && supervisorModule ? (
                        <>
                          {/* Hidden input to submit supervisor's module */}
                          <input type="hidden" value={supervisorModule} {...register('efficiency_type')} />
                          <div className="w-full px-3 py-2 border border-secondary-300 rounded-md bg-secondary-50 text-secondary-700">
                            {supervisorModule.replace(/_/g, ' ')}
                          </div>
                        </>
                      ) : (
                        <>
                          <select
                            id="efficiency_type"
                            {...register('efficiency_type')}
                            className="w-full px-3 py-2 border border-secondary-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                          >
                            <option value={EfficiencyTypeEnum.TIME_BASED}>Time Based</option>
                            <option value={EfficiencyTypeEnum.QUANTITY_BASED}>Quantity Based</option>
                            <option value={EfficiencyTypeEnum.TASK_BASED}>Task Based</option>
                          </select>
                          {errors.efficiency_type && (
                            <p className="mt-1 text-sm text-danger-600">{errors.efficiency_type.message}</p>
                          )}
                        </>
                      )}
                    </div>

                    {/* Conditional Fields */}
                    {efficiencyType === EfficiencyTypeEnum.TIME_BASED && !(isSupervisor && supervisorModule === EfficiencyTypeEnum.TASK_BASED) && (
                      <div>
                        <label htmlFor="std_hours_per_unit" className="block text-sm font-medium text-secondary-700 mb-1">
                          Expected Hours
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          id="std_hours_per_unit"
                          {...register('std_hours_per_unit', { valueAsNumber: true })}
                          className="w-full px-3 py-2 border border-secondary-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        />
                      </div>
                    )}

                    {efficiencyType === EfficiencyTypeEnum.QUANTITY_BASED && !(isSupervisor && supervisorModule === EfficiencyTypeEnum.TASK_BASED) && (
                      <div>
                        <label htmlFor="std_qty_per_hour" className="block text-sm font-medium text-secondary-700 mb-1">
                          Expected Quantity
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          id="std_qty_per_hour"
                          {...register('std_qty_per_hour', { valueAsNumber: true })}
                          className="w-full px-3 py-2 border border-secondary-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        />
                      </div>
                    )}

                    {/* Buttons */}
                    <div className="flex items-center justify-end space-x-3 pt-4 border-t border-secondary-200">
                      <button
                        type="button"
                        onClick={() => setModalOpen(false)}
                        className="px-4 py-2 border border-secondary-300 text-secondary-700 rounded-md hover:bg-secondary-50 transition-colors"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        disabled={submitting}
                        className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <Save className="w-4 h-4" />
                        <span>{submitting ? 'Saving...' : editingCode ? 'Update' : 'Create'}</span>
                      </button>
                    </div>
                  </form>
                </Dialog.Panel>
              </Transition.Child>
            </div>
          </div>
        </Dialog>
      </Transition>

      {/* Delete Confirmation Modal */}
      <Transition appear show={deleteModalOpen} as={Fragment}>
        <Dialog as="div" className="relative z-50" onClose={() => setDeleteModalOpen(false)}>
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
                  <Dialog.Title className="text-lg font-semibold text-secondary-900 mb-4">
                    Delete Activity Code
                  </Dialog.Title>

                  <p className="text-sm text-secondary-700 mb-6">
                    Are you sure you want to delete <strong>{deletingCode?.code}</strong>? This action cannot be
                    undone.
                  </p>

                  <div className="flex items-center justify-end space-x-3">
                    <button
                      type="button"
                      onClick={() => setDeleteModalOpen(false)}
                      className="px-4 py-2 border border-secondary-300 text-secondary-700 rounded-md hover:bg-secondary-50 transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={confirmDelete}
                      disabled={submitting}
                      className="px-4 py-2 bg-danger-600 text-white rounded-md hover:bg-danger-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {submitting ? 'Deleting...' : 'Delete'}
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

export default ActivityCodesPage;
