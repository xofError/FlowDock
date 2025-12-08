import { describe, it, expect, beforeEach, vi } from 'vitest';

describe('API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('should export api module', async () => {
    const { default: api } = await import('../api');
    expect(api).toBeDefined();
  });

  it('should have setTokens method', async () => {
    const { default: api } = await import('../api');
    expect(typeof api.setTokens).toBe('function');
  });

  it('should have clearTokens method', async () => {
    const { default: api } = await import('../api');
    expect(typeof api.clearTokens).toBe('function');
  });

  it('should have login method', async () => {
    const { default: api } = await import('../api');
    expect(typeof api.login).toBe('function');
  });

  it('should have register method', async () => {
    const { default: api } = await import('../api');
    expect(typeof api.register).toBe('function');
  });

  it('should have logout method', async () => {
    const { default: api } = await import('../api');
    expect(typeof api.logout).toBe('function');
  });

  it('should have verifyEmail method', async () => {
    const { default: api } = await import('../api');
    expect(typeof api.verifyEmail).toBe('function');
  });

  it('should have setupTOTP method', async () => {
    const { default: api } = await import('../api');
    expect(typeof api.setupTOTP).toBe('function');
  });

  it('should have verifyTOTP method', async () => {
    const { default: api } = await import('../api');
    expect(typeof api.verifyTOTP).toBe('function');
  });
});
