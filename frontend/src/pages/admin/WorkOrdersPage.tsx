import { useEffect, useState, Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import api from '../../services/api';
import toast from 'react-hot-toast';
import { WorkOrder, Machine } from '../../types';
import { Plus, Edit, Trash2, X, Save, Package } from 'lucide-react';

const workOrderSchema = z.object({
  wo_number: z.string().min(1, 'Work order number is required'),
  machine_id: z.number({ required_error: 'Machine is required' }).min(1, 'Please select a machine'),
  planned_qty: z.number({ required_error: 'Planned quantity is required' }).positive('Quantity must be positive'),
  msd_month: z.string().regex(/^\d{4}-\d{2}$/, 'MSD month must be in YYYY-MM format'),
});

type WorkOrderFormData = z.infer<typeof workOrderSchema>;

const WorkOrdersPage = () => {
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([]);
  const [machines, setMachines] = useState<Machine[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [editingWorkOrder, setEditingWorkOrder] = useState<WorkOrder | null>(null);
  const [deletingWorkOrder, setDeletingWorkOrder] = useState<WorkOrder | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<WorkOrderFormData>({
    resolver: zodResolver(workOrderSchema),
  });

  useEffect(() => {
    fetchWorkOrders();
    fetchMachines();
  }, []);

  const fetchWorkOrders = async () => {
    setLoading(true);
    try {
      const response = await api.get('/work-orders');
      setWorkOrders(response.data);
    } catch (error) {
      console.error('Failed to fetch work orders:', error);
      toast.error('Failed to load work orders');
    } finally {
      setLoading(false);
    }
  };

  const fetchMachines = async () => {
    try {
      const response = await api.get('/machines');
      setMachines(response.data);
    } catch (error) {
      console.error('Failed to fetch machines:', error);
      toast.error('Failed to load machines');
    }
  };

  const handleAdd = () => {
    setEditingWorkOrder(null);
    reset({
      wo_number: '',
      machine_id: undefined,
      planned_qty: 1,
      msd_month: new Date().toISOString().slice(0, 7), // Default to current month
    });
    setModalOpen(true);
  };

  const handleEdit = (workOrder: WorkOrder) => {
    setEditingWorkOrder(workOrder);
    reset({
      wo_number: workOrder.wo_number,
      machine_id: workOrder.machine_id,
      planned_qty: workOrder.planned_qty,
      msd_month: workOrder.msd_month,
    });
    setModalOpen(true);
  };

  const handleDeleteClick = (workOrder: WorkOrder) => {
    setDeletingWorkOrder(workOrder);
    setDeleteModalOpen(true);
  };

  const onSubmit = async (data: WorkOrderFormData) => {
    setSubmitting(true);
    try {
      if (editingWorkOrder) {
        await api.patch(`/work-orders/${editingWorkOrder.id}`, data);
        toast.success('Work order updated successfully');
      } else {
        await api.post('/work-orders', data);
        toast.success('Work order created successfully');
      }
      setModalOpen(false);
      fetchWorkOrders();
    } catch (error: any) {
      console.error('Failed to save work order:', error);
      toast.error(error.response?.data?.detail || 'Failed to save work order');
    } finally {
      setSubmitting(false);
    }
  };

  const confirmDelete = async () => {
    if (!deletingWorkOrder) return;

    setSubmitting(true);
    try {
      await api.delete(`/work-orders/${deletingWorkOrder.id}`);
      toast.success('Work order deleted successfully');
      setDeleteModalOpen(false);
      setDeletingWorkOrder(null);
      fetchWorkOrders();
    } catch (error: any) {
      console.error('Failed to delete work order:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete work order');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-secondary-900">Work Orders</h1>
          <p className="text-secondary-600 mt-1">Manage production work orders</p>
        </div>
        <button
          onClick={handleAdd}
          className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors"
        >
          <Plus className="w-5 h-5" />
          <span>Add Work Order</span>
        </button>
      </div>

      {/* Work Orders Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          </div>
        ) : workOrders.length === 0 ? (
          <div className="text-center py-12 text-secondary-500">
            <Package className="w-16 h-16 mx-auto mb-4 text-secondary-400" />
            <p className="text-lg font-medium">No work orders found</p>
            <p className="text-sm mt-2">Click "Add Work Order" to create one</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-secondary-200">
              <thead className="bg-secondary-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                    WO Number
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                    Machine
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                    MSD Month
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-secondary-700 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-secondary-200">
                {workOrders.map((wo) => (
                  <tr key={wo.id} className="hover:bg-secondary-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-secondary-900">
                      {wo.wo_number}
                    </td>
                    <td className="px-6 py-4 text-sm text-secondary-900">
                      {wo.machine_code && wo.machine_description
                        ? `${wo.machine_code} - ${wo.machine_description}`
                        : `Machine #${wo.machine_id}`}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary-900">
                      {wo.msd_month}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={() => handleEdit(wo)}
                          className="p-1 text-primary-600 hover:text-primary-700"
                          title="Edit"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteClick(wo)}
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
                      {editingWorkOrder ? 'Edit Work Order' : 'Add Work Order'}
                    </Dialog.Title>
                    <button
                      onClick={() => setModalOpen(false)}
                      className="text-secondary-400 hover:text-secondary-600"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>

                  <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    {/* WO Number */}
                    <div>
                      <label htmlFor="wo_number" className="block text-sm font-medium text-secondary-700 mb-1">
                        Work Order Number <span className="text-danger-600">*</span>
                      </label>
                      <input
                        type="text"
                        id="wo_number"
                        {...register('wo_number')}
                        className="w-full px-3 py-2 border border-secondary-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        placeholder="e.g., WO-2024-001"
                      />
                      {errors.wo_number && (
                        <p className="mt-1 text-sm text-danger-600">{errors.wo_number.message}</p>
                      )}
                    </div>

                    {/* Machine */}
                    <div>
                      <label htmlFor="machine_id" className="block text-sm font-medium text-secondary-700 mb-1">
                        Machine <span className="text-danger-600">*</span>
                      </label>
                      <select
                        id="machine_id"
                        {...register('machine_id', { valueAsNumber: true })}
                        className="w-full px-3 py-2 border border-secondary-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      >
                        <option value="">Select Machine</option>
                        {machines.map((machine) => (
                          <option key={machine.id} value={machine.id}>
                            {machine.machine_code} - {machine.description}
                          </option>
                        ))}
                      </select>
                      {errors.machine_id && (
                        <p className="mt-1 text-sm text-danger-600">{errors.machine_id.message}</p>
                      )}
                    </div>

                    {/* Planned Quantity field removed as requested (still sent with a default in payload) */}

                    {/* MSD Month */}
                    <div>
                      <label htmlFor="msd_month" className="block text-sm font-medium text-secondary-700 mb-1">
                        MSD Month <span className="text-danger-600">*</span>
                      </label>
                      <input
                        type="month"
                        id="msd_month"
                        {...register('msd_month')}
                        className="w-full px-3 py-2 border border-secondary-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      />
                      {errors.msd_month && (
                        <p className="mt-1 text-sm text-danger-600">{errors.msd_month.message}</p>
                      )}
                    </div>

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
                        <span>{submitting ? 'Saving...' : editingWorkOrder ? 'Update' : 'Create'}</span>
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
                    Delete Work Order
                  </Dialog.Title>

                  <p className="text-sm text-secondary-700 mb-6">
                    Are you sure you want to delete <strong>{deletingWorkOrder?.wo_number}</strong>? This action
                    cannot be undone and may affect related job cards.
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

export default WorkOrdersPage;
