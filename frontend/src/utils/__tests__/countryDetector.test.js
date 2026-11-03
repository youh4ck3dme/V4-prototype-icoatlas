import { describe, it, expect } from 'vitest';
import { detectCountryFromQuery } from '../countryDetector';

describe('detectCountryFromQuery', () => {
  it('detects CZ from prefix', () => {
    expect(detectCountryFromQuery('CZ27082440')).toBe('CZ');
    expect(detectCountryFromQuery('cz 27082440')).toBe('CZ');
    expect(detectCountryFromQuery('CZ12345678')).toBe('CZ');
  });

  it('detects SK from 8-digit IČO and switches to SK even if previously CZ', () => {
    expect(detectCountryFromQuery('88888888')).toBe('SK');
    expect(detectCountryFromQuery('88888888', 'CZ')).toBe('SK');
    expect(detectCountryFromQuery('51226511')).toBe('SK');
  });

  it('detects SK from Slovak DIČ format', () => {
    expect(detectCountryFromQuery('2020202020')).toBe('SK');
    expect(detectCountryFromQuery('1020304050')).toBe('SK');
    expect(detectCountryFromQuery('SK2020202020')).toBe('SK');
  });

  it('detects PL from NIP and Polish formats', () => {
    expect(detectCountryFromQuery('PL5260250274')).toBe('PL');
    expect(detectCountryFromQuery('526-025-02-74')).toBe('PL');
    expect(detectCountryFromQuery('KRS 0000123456')).toBe('PL');
    expect(detectCountryFromQuery('0000123456')).toBe('PL');
  });

  it('detects HU from Hungarian Adószám and formats', () => {
    expect(detectCountryFromQuery('HU12345678')).toBe('HU');
    expect(detectCountryFromQuery('12345678-1-42')).toBe('HU');
    expect(detectCountryFromQuery('01-09-123456')).toBe('HU');
  });

  it('returns null for ambiguous general queries', () => {
    expect(detectCountryFromQuery('')).toBeNull();
    expect(detectCountryFromQuery('Maly podnik s.r.o.')).toBeNull();
    expect(detectCountryFromQuery(null)).toBeNull();
  });
});
