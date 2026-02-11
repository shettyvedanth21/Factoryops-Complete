"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";

import {
  getDeviceAlerts,
  Alert,
  acknowledgeAlert,
  resolveAlert,
} from "@/lib/dataApi";
import { ApiError } from "@/components/ApiError";
import { EmptyState } from "@/components/EmptyState";

type AlertStatusFilter = "all" | "open" | "acknowledged" | "resolved";

export default function AlertsPage() {
  const params = useParams();
  const deviceId = params.deviceId as string;

  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);

  const [statusFilter, setStatusFilter] =
    useState<AlertStatusFilter>("all");

  const fetchAlerts = useCallback(async () => {
    if (!deviceId) return;

    setLoading(true);
    setError(null);

    try {
      const result = await getDeviceAlerts(deviceId, {
        page,
        pageSize,
        status: statusFilter === "all" ? undefined : statusFilter,
      });

      setAlerts(result.data);
      setTotal(result.total);
      setTotalPages(result.totalPages);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to fetch alerts"
      );
    } finally {
      setLoading(false);
    }
  }, [deviceId, page, pageSize, statusFilter]);

  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  useEffect(() => {
    setPage(1);
  }, [statusFilter]);

  /* ---------------- actions ---------------- */

  const handleAcknowledge = async (alertId: string) => {
    try {
      await acknowledgeAlert(alertId, "ui-user");
      await fetchAlerts();
    } catch (e) {
      alert("Failed to acknowledge alert");
    }
  };

  const handleResolve = async (alertId: string) => {
    try {
      await resolveAlert(alertId);
      await fetchAlerts();
    } catch (e) {
      alert("Failed to resolve alert");
    }
  };

  /* ---------------------------------------- */

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-zinc-900 dark:border-zinc-50 mx-auto" />
          <p className="mt-4 text-zinc-600 dark:text-zinc-400">
            Loading alerts...
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return <ApiError message={error} />;
  }

  return (
    <div className="space-y-4">

      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
          Device Alerts
        </h2>

        <div className="flex items-center gap-2">
          <label className="text-sm text-zinc-600 dark:text-zinc-400">
            Status
          </label>

          <select
            value={statusFilter}
            onChange={(e) =>
              setStatusFilter(e.target.value as AlertStatusFilter)
            }
            className="rounded-md border border-zinc-300 dark:border-zinc-700
                       bg-white dark:bg-zinc-900
                       px-3 py-1 text-sm"
          >
            <option value="all">All</option>
            <option value="open">Open</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="resolved">Resolved</option>
          </select>
        </div>
      </div>

      {alerts.length === 0 ? (
        <EmptyState message="No alerts found for this device." />
      ) : (
        <div className="bg-white dark:bg-zinc-900 rounded-lg shadow overflow-hidden">

          <table className="w-full">
            <thead className="bg-zinc-100 dark:bg-zinc-800">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase">
                  Time
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase">
                  Severity
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase">
                  Message
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase">
                  Actions
                </th>
              </tr>
            </thead>

            <tbody className="divide-y divide-zinc-200 dark:divide-zinc-700">
              {alerts.map((alert) => (
                <tr
                  key={alert.alertId}
                  className="hover:bg-zinc-50 dark:hover:bg-zinc-800/50"
                >
                  <td className="px-6 py-4 text-sm text-zinc-900 dark:text-zinc-100 whitespace-nowrap">
                    {new Date(alert.createdAt).toLocaleString()}
                  </td>

                  <td className="px-6 py-4 text-sm">
                    <span
                      className={`inline-flex px-2 py-1 rounded-full text-xs font-medium
                        ${
                          alert.severity === "critical"
                            ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300"
                            : alert.severity === "high"
                            ? "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300"
                            : "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300"
                        }
                      `}
                    >
                      {alert.severity}
                    </span>
                  </td>

                  <td className="px-6 py-4 text-sm text-zinc-900 dark:text-zinc-100">
                    {alert.message}
                  </td>

                  <td className="px-6 py-4 text-sm text-zinc-900 dark:text-zinc-100">
                    {alert.status}
                  </td>

                  <td className="px-6 py-4 text-sm">
                    <div className="flex gap-2">

                      {alert.status === "open" && (
                        <button
                          onClick={() => handleAcknowledge(alert.alertId)}
                          className="px-2 py-1 text-xs rounded border border-zinc-300 dark:border-zinc-700
                                     hover:bg-zinc-100 dark:hover:bg-zinc-800"
                        >
                          Acknowledge
                        </button>
                      )}

                      {alert.status !== "resolved" && (
                        <button
                          onClick={() => handleResolve(alert.alertId)}
                          className="px-2 py-1 text-xs rounded border border-zinc-300 dark:border-zinc-700
                                     hover:bg-zinc-100 dark:hover:bg-zinc-800"
                        >
                          Resolve
                        </button>
                      )}

                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="flex items-center justify-between px-6 py-3 border-t border-zinc-200 dark:border-zinc-700 text-sm">

            <div className="text-zinc-600 dark:text-zinc-400">
              {total} alerts • Page {page} of {totalPages}
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 rounded border border-zinc-300 dark:border-zinc-700
                           disabled:opacity-50"
              >
                Previous
              </button>

              <button
                onClick={() =>
                  setPage((p) => Math.min(totalPages, p + 1))
                }
                disabled={page >= totalPages}
                className="px-3 py-1 rounded border border-zinc-300 dark:border-zinc-700
                           disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}