/**
 * ICO Atlas DevTools Console Diagnostic Script
 * Vložte do konzoly prehliadača (F12 -> Console) na https://icoatlas.sk
 */
(async () => {
  const CONFIG = {
    apiBase: "https://api.icoatlas.sk",
    query: "88888888",
    country: "SK",
    graph: true,
  };

  const fieldSpec = [
    {
      group: "Core company",
      label: "Company name",
      paths: ["company.name", "company.company_name", "company.obchodne_meno", "company.title"],
      required: true,
      uiKeywords: ["Testovacia", "Firma", "s.r.o."],
    },
    {
      group: "Core company",
      label: "IČO",
      paths: ["company.ico", "company.ic", "company.registration_number", "company.id"],
      required: true,
      uiKeywords: [CONFIG.query],
    },
    {
      group: "Core company",
      label: "DIČ / NIP / Adószám",
      paths: ["company.dic", "company.tax_id", "company.nip", "company.adoszam"],
      required: true,
      uiKeywords: ["2020202020", "CZ27082440", "5260250995", "14906428-2-06"],
    },
    {
      group: "Core company",
      label: "VAT ID / IČ DPH",
      paths: ["company.vat_id", "company.ic_dph", "company.vat"],
      required: false,
      uiKeywords: ["IČ DPH", "VAT"],
    },
    {
      group: "Core company",
      label: "Country",
      paths: ["company.country", "country"],
      required: true,
      uiKeywords: ["SK", "Slovensko", "Slovakia"],
    },
    {
      group: "Core company",
      label: "Legal form",
      paths: ["company.legal_form", "company.form", "company.legalForm"],
      required: false,
      uiKeywords: ["s.r.o.", "spoločnosť", "legal form", "právna forma"],
    },
    {
      group: "Address",
      label: "Full address",
      paths: ["company.address", "company.full_address", "company.registered_address", "address"],
      required: true,
      uiKeywords: ["adresa", "sídlo", "address"],
    },
    {
      group: "Address",
      label: "Street",
      paths: ["company.address.street", "company.street"],
      required: false,
      uiKeywords: ["ulica", "street"],
    },
    {
      group: "Address",
      label: "City",
      paths: ["company.address.city", "company.city"],
      required: false,
      uiKeywords: ["mesto", "city"],
    },
    {
      group: "Address",
      label: "Postal code",
      paths: ["company.address.postal_code", "company.postal_code", "company.zip"],
      required: false,
      uiKeywords: ["PSČ", "postal"],
    },
    {
      group: "Registry metadata",
      label: "Provider status",
      paths: ["provider_status", "company.provider_status"],
      required: true,
      uiKeywords: ["live", "cached", "fallback", "Live", "Cached", "Fallback"],
    },
    {
      group: "Registry metadata",
      label: "Source provider",
      paths: ["provider", "source", "registry", "company.source"],
      required: false,
      uiKeywords: ["register", "registry", "RUZ", "ARES", "NAV", "KRS"],
    },
    {
      group: "Registry metadata",
      label: "Fallback warning",
      paths: ["fallback_reason", "warning", "provider_warning"],
      required: false,
      uiKeywords: ["fallback", "náhradný", "nedostupný", "register"],
    },
    {
      group: "Graph / related",
      label: "Related entities",
      paths: ["related", "related_companies", "graph.related", "graph.nodes", "relationships"],
      required: false,
      uiKeywords: ["Prepojené", "subjekty", "Related", "vzťah"],
    },
    {
      group: "Graph / related",
      label: "Graph nodes",
      paths: ["graph.nodes", "nodes"],
      required: false,
      uiKeywords: ["nodes", "graph", "prepojenia"],
    },
    {
      group: "Graph / related",
      label: "Graph edges",
      paths: ["graph.edges", "edges"],
      required: false,
      uiKeywords: ["edges", "relationship", "vzťah"],
    },
  ];

  const getByPath = (obj, path) => {
    if (!obj || !path) return undefined;
    const cleanPath = path.replace(/\s+/g, ".");
    return cleanPath.split(".").reduce((acc, key) => {
      if (acc === undefined || acc === null) return undefined;
      return acc[key];
    }, obj);
  };

  const isMeaningful = (value) => {
    if (value === undefined || value === null) return false;
    if (typeof value === "string") return value.trim().length > 0;
    if (Array.isArray(value)) return value.length > 0;
    if (typeof value === "object") return Object.keys(value).length > 0;
    return true;
  };

  const findApiValue = (data, paths) => {
    for (const path of paths) {
      const value = getByPath(data, path);
      if (isMeaningful(value)) return { path, value };
    }
    return { path: null, value: undefined };
  };

  const normalizeText = (text) =>
    String(text || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/\p{Diacritic}/gu, "");

  const pageText = normalizeText(document.body.innerText);

  const isVisibleInUi = (keywords, apiValue) => {
    const candidates = [];
    if (Array.isArray(keywords)) candidates.push(...keywords);
    if (typeof apiValue === "string") {
      candidates.push(apiValue);
    } else if (typeof apiValue === "number") {
      candidates.push(String(apiValue));
    } else if (apiValue && typeof apiValue === "object") {
      candidates.push(...Object.values(apiValue).filter((v) => typeof v === "string"));
    }
    return candidates.some((keyword) => {
      if (!keyword) return false;
      return pageText.includes(normalizeText(keyword));
    });
  };

  const url =
    `${CONFIG.apiBase}/api/v4/search/${encodeURIComponent(CONFIG.query)}` +
    `?country=${encodeURIComponent(CONFIG.country)}` +
    `${CONFIG.graph ? "&graph=1" : ""}`;

  console.log("%cICO Atlas Diagnostic", "font-size:18px;font-weight:bold;color:#38bdf8");
  console.log("API URL:", url);

  let data;
  try {
    const res = await fetch(url, { headers: { Accept: "application/json" } });
    console.log("HTTP:", res.status, res.statusText);

    if (!res.ok) {
      const text = await res.text();
      console.error("API failed:", text);
      return;
    }
    data = await res.json();
  } catch (error) {
    console.error("Fetch failed:", error);
    return;
  }

  const rows = fieldSpec.map((spec) => {
    const api = findApiValue(data, spec.paths);
    const apiHasValue = isMeaningful(api.value);
    const uiVisible = isVisibleInUi(spec.uiKeywords, api.value);

    let state = "MISSING";
    if (apiHasValue && uiVisible) state = "PASS";
    else if (apiHasValue && !uiVisible) state = "API_ONLY";
    else if (!apiHasValue && uiVisible) state = "UI_ONLY";

    return {
      group: spec.group,
      field: spec.label,
      required: spec.required ? "yes" : "no",
      state,
      apiPath: api.path || "-",
      apiValue:
        typeof api.value === "object"
          ? JSON.stringify(api.value).slice(0, 180)
          : String(api.value ?? "-").slice(0, 180),
      uiVisible: uiVisible ? "yes" : "no",
    };
  });

  console.table(rows);

  const summary = rows.reduce(
    (acc, row) => {
      acc.total += 1;
      acc[row.state] = (acc[row.state] || 0) + 1;
      if (row.required === "yes" && row.state !== "PASS") acc.requiredProblems += 1;
      return acc;
    },
    { total: 0, PASS: 0, API_ONLY: 0, UI_ONLY: 0, MISSING: 0, requiredProblems: 0 }
  );

  console.table([summary]);

  const missingRequired = rows.filter((row) => row.required === "yes" && row.state !== "PASS");
  if (missingRequired.length) {
    console.warn("Required fields not fully visible:");
    console.table(missingRequired);
  } else {
    console.log("%cAll required fields are visible.", "color:#22c55e;font-weight:bold");
  }

  console.log("Raw API response:");
  console.log(data);

  window.__ICOATLAS_LAST_DIAGNOSTIC__ = {
    config: CONFIG,
    url,
    rows,
    summary,
    raw: data,
    createdAt: new Date().toISOString(),
  };

  console.log(
    "%cSaved to window.__ICOATLAS_LAST_DIAGNOSTIC__",
    "color:#a78bfa;font-weight:bold"
  );
})();
