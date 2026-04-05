const DEFAULT_TTL_MS = 5 * 60 * 1000;
const FILES_TTL_MS = 30 * 1000;

export const DEFAULT_SAMPLE_STEP = 4;
export const DEMO_LOCATION_CODES = ["SHARK", "SHINJUKU1"];

const SELECTED_REPLAY_STORAGE_KEY = "trafficlab.selectedReplayPath";

const filesCache = {
  expiresAt: 0,
  value: null,
};

const analyticsCache = new Map();
const disasterCache = new Map();
const inFlight = new Map();

function nowMs() {
  return Date.now();
}

function getCached(map, key) {
  const entry = map.get(key);
  if (!entry) {
    return null;
  }
  if (entry.expiresAt <= nowMs()) {
    map.delete(key);
    return null;
  }
  return entry.value;
}

function setCached(map, key, value, ttlMs) {
  map.set(key, {
    value,
    expiresAt: nowMs() + Math.max(1000, Number(ttlMs || DEFAULT_TTL_MS)),
  });
}

function requestKey(prefix, path, sampleStep) {
  return `${prefix}|${path}|${sampleStep}`;
}

function normalizePath(path) {
  return String(path || "")
    .replace(/\\/g, "/")
    .trim();
}

export function isDemoReplayPath(path) {
  const normalized = normalizePath(path).toUpperCase();
  if (!normalized) {
    return false;
  }
  return DEMO_LOCATION_CODES.some((code) => normalized.includes(`/${code}/`));
}

export function filterDemoVisualizationFiles(files) {
  const list = Array.isArray(files) ? files : [];
  return list.filter((item) => isDemoReplayPath(item?.path));
}

export function getStoredReplayPath() {
  try {
    return normalizePath(
      window.localStorage.getItem(SELECTED_REPLAY_STORAGE_KEY),
    );
  } catch {
    return "";
  }
}

export function persistSelectedReplayPath(path) {
  const value = normalizePath(path);
  try {
    if (!value) {
      window.localStorage.removeItem(SELECTED_REPLAY_STORAGE_KEY);
      return;
    }
    window.localStorage.setItem(SELECTED_REPLAY_STORAGE_KEY, value);
  } catch {
    // Ignore storage failures in restricted browser contexts.
  }
}

export function resolveReplaySelection({ queryPath = "", files = [] } = {}) {
  const list = filterDemoVisualizationFiles(files);
  const allowed = new Set(list.map((item) => normalizePath(item.path)));
  const q = normalizePath(queryPath);
  if (q && allowed.has(q)) {
    return q;
  }

  const stored = getStoredReplayPath();
  if (stored && allowed.has(stored)) {
    return stored;
  }
  return "";
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

export async function fetchVisualizationFiles({ force = false } = {}) {
  const isFresh = filesCache.value !== null && filesCache.expiresAt > nowMs();
  if (!force && isFresh) {
    return filesCache.value;
  }

  const key = "files";
  const pending = inFlight.get(key);
  if (pending) {
    return pending;
  }

  const promise = fetchJson("/api/visualization/files")
    .then((data) => {
      const list = Array.isArray(data) ? data : [];
      filesCache.value = list;
      filesCache.expiresAt = nowMs() + FILES_TTL_MS;
      return list;
    })
    .finally(() => {
      inFlight.delete(key);
    });

  inFlight.set(key, promise);
  return promise;
}

export async function fetchAnalytics(
  path,
  {
    sampleStep = DEFAULT_SAMPLE_STEP,
    ttlMs = DEFAULT_TTL_MS,
    force = false,
  } = {},
) {
  if (!path) {
    return null;
  }

  const step = Math.max(1, Number(sampleStep || DEFAULT_SAMPLE_STEP));
  const key = requestKey("analytics", path, step);

  if (!force) {
    const cached = getCached(analyticsCache, key);
    if (cached) {
      return cached;
    }

    const pending = inFlight.get(key);
    if (pending) {
      return pending;
    }
  }

  const url = `/api/visualization/analytics?path=${encodeURIComponent(path)}&sample_step=${step}`;
  const promise = fetchJson(url)
    .then((data) => {
      setCached(analyticsCache, key, data, ttlMs);
      return data;
    })
    .finally(() => {
      inFlight.delete(key);
    });

  inFlight.set(key, promise);
  return promise;
}

export async function fetchDisasterManagement(
  path,
  {
    sampleStep = DEFAULT_SAMPLE_STEP,
    ttlMs = DEFAULT_TTL_MS,
    force = false,
  } = {},
) {
  if (!path) {
    return null;
  }

  const step = Math.max(1, Number(sampleStep || DEFAULT_SAMPLE_STEP));
  const key = requestKey("disaster", path, step);

  if (!force) {
    const cached = getCached(disasterCache, key);
    if (cached) {
      return cached;
    }

    const pending = inFlight.get(key);
    if (pending) {
      return pending;
    }
  }

  const url = `/api/visualization/disaster-management?path=${encodeURIComponent(path)}&sample_step=${step}`;
  const promise = fetchJson(url)
    .then((data) => {
      setCached(disasterCache, key, data, ttlMs);
      return data;
    })
    .finally(() => {
      inFlight.delete(key);
    });

  inFlight.set(key, promise);
  return promise;
}

export function prefetchAnalytics(path, opts = {}) {
  if (!path) {
    return;
  }
  fetchAnalytics(path, opts).catch(() => {});
}

export function prefetchDisasterManagement(path, opts = {}) {
  if (!path) {
    return;
  }
  fetchDisasterManagement(path, opts).catch(() => {});
}

export function preloadDashboardData(path, opts = {}) {
  if (!path) {
    return;
  }
  prefetchAnalytics(path, opts);
  prefetchDisasterManagement(path, opts);
}

export function preloadDemoDashboardData(selectedPath, files, opts = {}) {
  const list = filterDemoVisualizationFiles(files);
  if (!list.length) {
    return;
  }

  const selected = normalizePath(selectedPath);
  const paths = list.map((item) => normalizePath(item.path)).filter(Boolean);
  const ordered =
    selected && paths.includes(selected)
      ? [selected, ...paths.filter((p) => p !== selected)]
      : paths;

  for (const path of ordered) {
    preloadDashboardData(path, opts);
  }
}
