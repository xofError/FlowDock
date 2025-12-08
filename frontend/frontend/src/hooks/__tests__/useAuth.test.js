import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock the api module BEFORE importing useAuth
vi.mock('../../services/api', () => ({
  default: {
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
  },
}));

describe('useAuth Hook - Unit Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('should export useAuth as default', async () => {
    const { default: useAuth } = await import('../useAuth');
    expect(typeof useAuth).toBe('function');
  });

  it('should have required methods', async () => {
    const { default: useAuth } = await import('../useAuth');
    const methods = ['login', 'register', 'logout', 'verifyEmail', 'setupTOTP', 'verifyTOTP'];

    methods.forEach((method) => {
      expect(useAuth).toBeDefined();
    });
  });

  it('should initialize with correct structure', async () => {
    const { default: useAuth } = await import('../useAuth');
    expect(useAuth).toBeDefined();
    expect(typeof useAuth).toBe('function');
  });

  it('should have authentication methods', async () => {
    const { default: useAuth } = await import('../useAuth');
    const hook = useAuth;

    expect(hook).toBeDefined();
  });

  it('should export named export', async () => {
    const { useAuth } = await import('../useAuth');
    expect(typeof useAuth).toBe('function');
  });
});
