/**
 * V4 Country & Jurisdiction Auto-Detector for Business Identifiers
 * 
 * Intelligently classifies input query strings into corresponding V4 jurisdictions:
 * - SK (Slovakia): standard 8-digit IČO, SK DIČ (10 digits starting with 20/10/11), SK prefix, .sk domain
 * - CZ (Czechia): CZ prefix (DIČ / IČO e.g. CZ27082440), .cz domain, preserves manual CZ selection for 8-digit IČO
 * - PL (Poland): PL prefix, NIP (10 digits, formatted XXX-XXX-XX-XX), KRS, 9/14-digit REGON, .pl domain
 * - HU (Hungary): HU prefix, Adószám (XXXXXXXX-Y-ZZ or 11 digits), Cégjegyzékszám (XX-YY-ZZZZZZ), .hu domain
 */

export const detectCountryFromQuery = (input, currentCountry = "SK", isManualSelection = false) => {
  if (!input || typeof input !== "string") return null;

  const raw = input.trim().toUpperCase();
  if (!raw) return null;

  // Clean alphanumeric string
  const clean = raw.replace(/[\s\.\-\/]/g, "");

  // 1. Explicit country prefixes (Tax ID, VAT, IBAN or National Prefixes)
  if (raw.startsWith("CZ") || clean.startsWith("CZ")) return "CZ";
  if (raw.startsWith("SK") || clean.startsWith("SK")) return "SK";
  if (raw.startsWith("PL") || clean.startsWith("PL")) return "PL";
  if (raw.startsWith("HU") || clean.startsWith("HU")) return "HU";

  // 2. Czech specific format patterns
  if (raw.endsWith(".CZ")) return "CZ";

  // 3. Slovak specific format patterns
  if (raw.endsWith(".SK")) return "SK";
  // Slovak DIČ: 10 digits starting with 20, 10, or 11
  if (/^(20|10|11)\d{8}$/.test(clean)) return "SK";

  // 4. Polish specific format patterns
  // Formatted NIP (e.g. 123-456-78-19 or 123-45-67-819)
  if (/^\d{3}-\d{3}-\d{2}-\d{2}$/.test(raw) || /^\d{3}-\d{2}-\d{2}-\d{3}$/.test(raw)) return "PL";
  // KRS: e.g. "KRS 0000123456" or "0000" + 6 digits
  if (/^KRS\s*\d+$/i.test(raw) || /^0000\d{6}$/.test(clean)) return "PL";
  // 9-digit or 14-digit REGON
  if (/^\d{9}$/.test(clean) || /^\d{14}$/.test(clean)) return "PL";
  if (raw.endsWith(".PL")) return "PL";

  // 5. Hungarian specific format patterns
  // Adószám: 8 digits - 1 digit - 2 digits (e.g. 12345678-1-42 or 11 digits)
  if (/^\d{8}-\d-\d{2}$/.test(raw) || /^\d{11}$/.test(clean)) return "HU";
  // Cégjegyzékszám: 01-09-123456 (2 digits - 2 digits - 6 digits)
  if (/^\d{2}-\d{2}-\d{6}$/.test(raw)) return "HU";
  if (raw.endsWith(".HU")) return "HU";

  // 6. Standard 8-digit numeric IČO
  if (/^\d{8}$/.test(clean)) {
    // If user explicitly manually clicked CZ, preserve CZ; otherwise auto-detect SK
    if (isManualSelection && currentCountry === "CZ") {
      return "CZ";
    }
    return "SK";
  }

  // 7. 6-digit historical Slovak IČO
  if (/^\d{6}$/.test(clean)) {
    return "SK";
  }

  return null;
};
