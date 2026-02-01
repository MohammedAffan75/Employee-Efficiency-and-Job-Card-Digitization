import api from './api';
import { JobCard, CreateJobCardRequest } from '../types';

export const jobCardService = {
  /**
   * Get all jobcards with optional filters
   */
  async getJobCards(params?: {
    start_date?: string;
    end_date?: string;
    employee_id?: number;
    has_flags?: boolean;
  }): Promise<JobCard[]> {
    const response = await api.get<JobCard[]>('/jobcards', { params });
    return response.data;
  },

  /**
   * Create a new jobcard
   */
  async createJobCard(data: CreateJobCardRequest): Promise<JobCard> {
    const response = await api.post<JobCard>('/jobcards', data);
    return response.data;
  },

  /**
   * Update a jobcard
   */
  async updateJobCard(id: number, data: Partial<CreateJobCardRequest>): Promise<JobCard> {
    const response = await api.patch<JobCard>(`/jobcards/${id}`, data);
    return response.data;
  },

  /**
   * Delete a jobcard
   */
  async deleteJobCard(id: number): Promise<void> {
    await api.delete(`/jobcards/${id}`);
  },
};
