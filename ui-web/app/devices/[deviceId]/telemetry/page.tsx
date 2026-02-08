"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useParams } from "next/navigation";
import { getTelemetry } from "@/lib/dataApi";
import { ApiError } from "@/components/ApiError";
import { EmptyState } from "@/components/EmptyState";

interface TelemetryData {
  timestamp: string;
  voltage: number;
  current: number;
  power: number;
  temperature: number;
}

export default function TelemetryPage() {
  const params = useParams();
  const deviceId = params.deviceId as string;

  const [data, setData] = useState<TelemetryData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchTelemetry = useCallback(async (isRefresh = false) => {
    if (!isRefresh) {
      setLoading(true);
    }
    setError(null);

    try {
      const result = await getTelemetry(deviceId, {
        limit: "20",
      });

      const rows = Array.isArray(result)
        ? result
        : result?.data ?? [];

      setData(rows);
      setLastUpdated(new Date());
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to fetch telemetry data"
      );
    } finally {
      if (!isRefresh) {
        setLoading(false);
      }
    }
  }, [deviceId]);

  useEffect(() => {
    if (!deviceId) return;

    // Initial fetch
    fetchTelemetry(false);

    // Set up auto-refresh every 5 seconds
    intervalRef.current = setInterval(() => {
      fetchTelemetry(true);
    }, 5000);

    // Clear interval on unmount
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [deviceId, fetchTelemetry]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-zinc-900 dark:border-zinc-50 mx-auto"></div>
          <p className="mt-4 text-zinc-600 dark:text-zinc-400">
            Loading telemetry data...
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return <ApiError message={error} />;
  }

  return (
    <div className="bg-white dark:bg-zinc-900 rounded-lg shadow overflow-hidden">
      <div className="px-6 py-4 border-b border-zinc-200 dark:border-zinc-700 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
          Latest Telemetry Data
        </h2>
        {lastUpdated && (
          <span className="text-sm text-zinc-500 dark:text-zinc-400">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </span>
        )}
      </div>

      <table className="w-full">
        <thead className="bg-zinc-100 dark:bg-zinc-800">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">
              Timestamp
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">
              Voltage
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">
              Current
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">
              Power
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">
              Temperature
            </th>
          </tr>
        </thead>

        <tbody className="divide-y divide-zinc-200 dark:divide-zinc-700">
          {data.length === 0 ? (
            <tr>
              <td
                colSpan={5}
                className="px-6 py-8"
              >
                <EmptyState message="No telemetry data available" />
              </td>
            </tr>
          ) : (
            data.map((row, index) => (
              <tr
                key={index}
                className="hover:bg-zinc-50 dark:hover:bg-zinc-800/50"
              >
                <td className="px-6 py-4 whitespace-nowrap text-sm text-zinc-900 dark:text-zinc-100">
                  {new Date(row.timestamp).toLocaleString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-zinc-900 dark:text-zinc-100">
                  {row.voltage} V
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-zinc-900 dark:text-zinc-100">
                  {row.current} A
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-zinc-900 dark:text-zinc-100">
                  {row.power} W
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-zinc-900 dark:text-zinc-100">
                  {row.temperature} °C
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
