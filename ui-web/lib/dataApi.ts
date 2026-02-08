import { DATA_SERVICE_BASE } from "./api";

/* ---------- telemetry ---------- */

export async function getTelemetry(
  deviceId: string,
  params?: Record<string, string>
) {
  const query = new URLSearchParams(params || {}).toString();

  const url =
    `${DATA_SERVICE_BASE}/api/data/devices/${deviceId}/telemetry` +
    (query ? `?${query}` : "");

  const res = await fetch(url);

  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }

  return res.json();
}

/* ---------- stats ---------- */

export async function getDeviceStats(deviceId: string) {
  const res = await fetch(
    `${DATA_SERVICE_BASE}/api/data/devices/${deviceId}/stats`
  );

  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }

  return res.json();
}
