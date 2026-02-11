import { DATA_EXPORT_SERVICE_BASE } from "./api";

export async function runExport(deviceId: string) {
  const res = await fetch(
    `${DATA_EXPORT_SERVICE_BASE}/api/v1/exports/run`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ device_id: deviceId }),
    }
  );

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Export failed");
  }

  return res.json();
}

export async function getExportStatus(deviceId: string) {
  const res = await fetch(
    `${DATA_EXPORT_SERVICE_BASE}/api/v1/exports/status/${deviceId}`
  );

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Failed to get export status");
  }

  return res.json();
}