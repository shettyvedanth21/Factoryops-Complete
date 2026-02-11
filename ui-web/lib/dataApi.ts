import { DATA_SERVICE_BASE, RULE_ENGINE_SERVICE_BASE } from "./api";

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

/* ---------- alerts (rule-engine-service) ---------- */

export interface Alert {
  alertId: string;
  ruleId: string;
  deviceId: string;
  severity: string;
  message: string;
  actualValue: number;
  thresholdValue: number;
  status: string;
  acknowledgedBy: string | null;
  acknowledgedAt: string | null;
  resolvedAt: string | null;
  createdAt: string;
}

export async function getDeviceAlerts(
  deviceId: string,
  params?: {
    page?: number;
    pageSize?: number;
    status?: string;
  }
): Promise<{
  data: Alert[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}> {

  const query = new URLSearchParams({
    device_id: deviceId,
    page: String(params?.page ?? 1),
    page_size: String(params?.pageSize ?? 20),
  });

  if (params?.status) {
    query.append("status", params.status);
  }

  const res = await fetch(
    `${RULE_ENGINE_SERVICE_BASE}/api/v1/alerts?${query.toString()}`
  );

  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }

  const json = await res.json();

  return {
    data: json.data.map((a: any) => ({
      alertId: a.alert_id,
      ruleId: a.rule_id,
      deviceId: a.device_id,
      severity: a.severity,
      message: a.message,
      actualValue: a.actual_value,
      thresholdValue: a.threshold_value,
      status: a.status,
      acknowledgedBy: a.acknowledged_by,
      acknowledgedAt: a.acknowledged_at,
      resolvedAt: a.resolved_at,
      createdAt: a.created_at,
    })),
    total: json.total,
    page: json.page,
    pageSize: json.page_size,
    totalPages: json.total_pages,
  };
}


/* ---------- alert actions ---------- */

export async function acknowledgeAlert(
  alertId: string,
  acknowledgedBy: string
) {
  const res = await fetch(
    `${RULE_ENGINE_SERVICE_BASE}/api/v1/alerts/${alertId}/acknowledge`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        acknowledged_by: acknowledgedBy,
      }),
    }
  );

  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }

  return res.json();
}

export async function resolveAlert(alertId: string) {
  const res = await fetch(
    `${RULE_ENGINE_SERVICE_BASE}/api/v1/alerts/${alertId}/resolve`,
    {
      method: "PATCH",
    }
  );

  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }

  return res.json();
}