import { vi } from 'vitest';

export const mockApi = {
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
  getCurrentUser: vi.fn(),
  verifyEmail: vi.fn(),
  requestPasswordReset: vi.fn(),
  resetPassword: vi.fn(),
  setupTOTP: vi.fn(),
  verifyTOTP: vi.fn(),
  setTokens: vi.fn(),
  clearTokens: vi.fn(),
};

export default mockApi;
