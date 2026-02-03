import { create } from 'zustand';
import { researchAPI } from '../services/api';
import type { ResearchProject, ResearchTask, ResearchResult } from '../types';

interface ResearchState {
  projects: ResearchProject[];
  tasks: ResearchTask[];
  currentTask: ResearchTask | null;
  currentResult: ResearchResult | null;
  loading: boolean;
  error: string | null;

  fetchProjects: () => Promise<void>;
  createProject: (data: { name: string; description?: string }) => Promise<ResearchProject>;
  startResearch: (companyName: string, projectId?: number) => Promise<{ task_id: string; task: ResearchTask }>;
  fetchTasks: (params?: { status?: string; search?: string }) => Promise<void>;
  fetchTaskStatus: (taskId: string) => Promise<ResearchTask>;
  fetchTaskResult: (taskId: string) => Promise<ResearchResult>;
  setCurrentTask: (task: ResearchTask | null) => void;
  clearError: () => void;
}

export const useResearchStore = create<ResearchState>((set) => ({
  projects: [],
  tasks: [],
  currentTask: null,
  currentResult: null,
  loading: false,
  error: null,

  fetchProjects: async () => {
    set({ loading: true, error: null });
    try {
      const response = await researchAPI.getProjects();
      set({ projects: response.data, loading: false });
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Failed to fetch projects';
      set({ error: message, loading: false });
    }
  },

  createProject: async (data) => {
    set({ loading: true, error: null });
    try {
      const response = await researchAPI.createProject(data);
      set((state) => ({
        projects: [...state.projects, response.data],
        loading: false,
      }));
      return response.data;
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Failed to create project';
      set({ error: message, loading: false });
      throw new Error(message);
    }
  },

  startResearch: async (companyName: string, projectId?: number) => {
    set({ loading: true, error: null });
    try {
      const response = await researchAPI.startResearch({
        company_name: companyName,
        project_id: projectId,
      });
      const { task_id, task } = response.data;
      set((state) => ({
        tasks: [task, ...state.tasks],
        currentTask: task,
        loading: false,
      }));
      return { task_id, task };
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Failed to start research';
      set({ error: message, loading: false });
      throw new Error(message);
    }
  },

  fetchTasks: async (params) => {
    set({ loading: true, error: null });
    try {
      const response = await researchAPI.getTasks(params);
      set({ tasks: response.data, loading: false });
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Failed to fetch tasks';
      set({ error: message, loading: false });
    }
  },

  fetchTaskStatus: async (taskId: string) => {
    try {
      const response = await researchAPI.getTask(taskId);
      const task = response.data;
      set((state) => ({
        tasks: state.tasks.map((t) => (t.task_id === taskId ? task : t)),
        currentTask: state.currentTask?.task_id === taskId ? task : state.currentTask,
      }));
      return task;
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Failed to fetch task status';
      set({ error: message });
      throw new Error(message);
    }
  },

  fetchTaskResult: async (taskId: string) => {
    set({ loading: true, error: null });
    try {
      const response = await researchAPI.getTaskResult(taskId);
      set({ currentResult: response.data, loading: false });
      return response.data;
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Failed to fetch results';
      set({ error: message, loading: false });
      throw new Error(message);
    }
  },

  setCurrentTask: (task) => set({ currentTask: task }),

  clearError: () => set({ error: null }),
}));
