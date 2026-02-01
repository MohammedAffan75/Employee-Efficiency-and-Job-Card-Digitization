import { useEffect, useState, Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import api from '../../services/api';
import toast from 'react-hot-toast';
import { Machine } from '../../types';
import { Plus, Edit, Trash2, X, Save, Settings } from 'lucide-react';
import { useRole } from '../../hooks/useRole';

const machineSchema = z.object({
  machine_code: z.string().min(1, 'Machine code is required'),
  description: z.string().min(1, 'Description is required'),
  work_center: z.string().min(1, 'Work center is required'),
});

type MachineFormData = z.infer<typeof machineSchema>;

const MachinesPage = () => {
  const { isSupervisor } = useRole();
  const [machines, setMachines] = useState<Machine[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [editingMachine, setEditingMachine] = useState<Machine | null>(null);
  const [deletingMachine, setDeletingMachine] = useState<Machine | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<MachineFormData>({
    resolver: zodResolver(machineSchema),
  });

  useEffect(() => {
    fetchMachines();
  }, []);

  const fetchMachines = async () => {
    setLoading(true);
    try {
      const response = await api.get('/machines');
      setMachines(response.data);
    } catch (error) {
      console.error('Failed to fetch machines:', error);
      toast.error('Failed to load machines');
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = () => {
    setEditingMachine(null);
    reset({
      machine_code: '',
      description: '',
      work_center: '',
    });
    setModalOpen(true);
  };

  const handleEdit = (machine: Machine) => {
    setEditingMachine(machine);
    reset({
      machine_code: machine.machine_code,
      description: machine.description,
      work_center: machine.work_center,
    });
    setModalOpen(true);
  };

  const handleDeleteClick = (machine: Machine) => {
    setDeletingMachine(machine);
    setDeleteModalOpen(true);
  };

  const onSubmit = async (data: MachineFormData) => {
    setSubmitting(true);
    try {
      if (editingMachine) {
        await api.patch(`/machines/${editingMachine.id}`, data);
        toast.success('Machine updated successfully');
      } else {
        await api.post('/machines', data);
        toast.success('Machine created successfully');
      }
      setModalOpen(false);
      fetchMachines();
    } catch (error: any) {
      console.error('Failed to save machine:', error);
      toast.error(error.response?.data?.detail || 'Failed to save machine');
    } finally {
      setSubmitting(false);
    }
  };

  const confirmDelete = async () => {
    if (!deletingMachine) return;

    setSubmitting(true);
    try {
      await api.delete(`/machines/${deletingMachine.id}`);
      toast.success('Machine deleted successfully');
      setDeleteModalOpen(false);
      setDeletingMachine(null);
      fetchMachines();
    } catch (error: any) {
      console.error('Failed to delete machine:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete machine');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-secondary-900">Machines</h1>
          <p className="text-secondary-600 mt-1">Manage machine master data</p>
        </div>
        {isSupervisor && (
          <button
            onClick={handleAdd}
            className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors"
          >
            <Plus className="w-5 h-5" />
            <span>Add Machine</span>
          </button>
        )}
      </div>

      {/* Machines Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          </div>
        ) : machines.length === 0 ? (
          <div className="text-center py-12 text-secondary-500">
            <Settings className="w-16 h-16 mx-auto mb-4 text-secondary-400" />
            <p className="text-lg font-medium">No machines found</p>
            <p className="text-sm mt-2">Click "Add Machine" to create one</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-secondary-200">
              <thead className="bg-secondary-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                    Machine Code
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                    Description
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-secondary-700 uppercase tracking-wider">
                    Work Center
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-secondary-700 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-secondary-200">
                {machines.map((machine) => (
                  <tr key={machine.id} className="hover:bg-secondary-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-secondary-900">
                      {machine.machine_code}
                    </td>
                    <td className="px-6 py-4 text-sm text-secondary-900">{machine.description}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary-900">
                      {machine.work_center}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={() => handleEdit(machine)}
                          className="p-1 text-primary-600 hover:text-primary-700"
                          title="Edit"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteClick(machine)}
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
                      {editingMachine ? 'Edit Machine' : 'Add Machine'}
                    </Dialog.Title>
                    <button
                      onClick={() => setModalOpen(false)}
                      className="text-secondary-400 hover:text-secondary-600"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>

                  <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    {/* Machine Code */}
                    <div>
                      <label htmlFor="machine_code" className="block text-sm font-medium text-secondary-700 mb-1">
                        Machine Code <span className="text-danger-600">*</span>
                      </label>
                      <input
                        type="text"
                        id="machine_code"
                        {...register('machine_code')}
                        className="w-full px-3 py-2 border border-secondary-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        placeholder="e.g., M001"
                      />
                      {errors.machine_code && (
                        <p className="mt-1 text-sm text-danger-600">{errors.machine_code.message}</p>
                      )}
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
                        placeholder="e.g., CNC Machine 1"
                      />
                      {errors.description && (
                        <p className="mt-1 text-sm text-danger-600">{errors.description.message}</p>
                      )}
                    </div>

                    {/* Work Center */}
                    <div>
                      <label htmlFor="work_center" className="block text-sm font-medium text-secondary-700 mb-1">
                        Work Center <span className="text-danger-600">*</span>
                      </label>
                      <input
                        type="text"
                        id="work_center"
                        {...register('work_center')}
                        className="w-full px-3 py-2 border border-secondary-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                        placeholder="e.g., WC01"
                      />
                      {errors.work_center && (
                        <p className="mt-1 text-sm text-danger-600">{errors.work_center.message}</p>
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
                        <span>{submitting ? 'Saving...' : editingMachine ? 'Update' : 'Create'}</span>
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
                    Delete Machine
                  </Dialog.Title>

                  <p className="text-sm text-secondary-700 mb-6">
                    Are you sure you want to delete <strong>{deletingMachine?.machine_code}</strong>? This action
                    cannot be undone.
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

export default MachinesPage;
