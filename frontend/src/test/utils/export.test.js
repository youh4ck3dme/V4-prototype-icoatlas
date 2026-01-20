import { describe, it, expect } from 'vitest';

// Test utility functions
describe('Export Utilities', () => {
  it('should validate ICO format', () => {
    const isValidICO = (ico) => /^\d{8}$/.test(ico);
    
    expect(isValidICO('12345678')).toBe(true);
    expect(isValidICO('1234567')).toBe(false);
    expect(isValidICO('123456789')).toBe(false);
    expect(isValidICO('abcdefgh')).toBe(false);
  });

  it('should format company name correctly', () => {
    const formatName = (name) => name?.trim() || 'N/A';
    
    expect(formatName('Test Company')).toBe('Test Company');
    expect(formatName('  Spaced Name  ')).toBe('Spaced Name');
    expect(formatName(null)).toBe('N/A');
    expect(formatName(undefined)).toBe('N/A');
  });
});
