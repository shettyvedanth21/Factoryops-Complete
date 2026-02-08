"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getDeviceStats } from "@/lib/dataApi";
import { ApiError } from "@/components/ApiError";
import { EmptyState } from "@/components/EmptyState";

/* ---------- backend response ---------- */

interface BackendDeviceStats {
  device_id: string;
  start_time: string;
  end_time: string;

  voltage_min: number;
  voltage_max: number;
  voltage_avg: number;

  current_min: number;
  current_max: number;
  current_avg: number;

  power_min: number;
  power_max: number;
  power_avg: number;
  power_total: number;

  temperature_min: number;
  temperature_max: number;
  temperature_avg: number;

  data_points: number;
}

/* ---------- UI model ---------- */

interface StatMetric {
  min: number;
  max: number;
  avg: number;
}

interface PowerMetric extends StatMetric {
  total: number;
}

interface DeviceStats {
  voltage: StatMetric;
  current: StatMetric;
  power: PowerMetric;
  temperature: StatMetric;
  data_points: number;
  start_time: string;
  end_time: string;
}

export default function StatsPage() {
  const params = useParams();
  const deviceId = params.deviceId as string;

  const [stats, setStats] = useState<DeviceStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!deviceId) return;

    const fetchStats = async () => {
      setLoading(true);
      setError(null);

      try {
        const raw = (await getDeviceStats(
          deviceId
        )) as BackendDeviceStats;

        const mapped: DeviceStats = {
          voltage: {
            min: raw.voltage_min,
            max: raw.voltage_max,
            avg: raw.voltage_avg,
          },
          current: {
            min: raw.current_min,
            max: raw.current_max,
            avg: raw.current_avg,
          },
          power: {
            min: raw.power_min,
            max: raw.power_max,
            avg: raw.power_avg,
            total: raw.power_total,
          },
          temperature: {
            min: raw.temperature_min,
            max: raw.temperature_max,
            avg: raw.temperature_avg,
          },
          data_points: raw.data_points,
          start_time: raw.start_time,
          end_time: raw.end_time,
        };

        setStats(mapped);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to fetch device stats"
        );
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [deviceId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-zinc-900 dark:border-zinc-50 mx-auto" />
          <p className="mt-4 text-zinc-600 dark:text-zinc-400">
            Loading device stats...
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return <ApiError message={error} />;
  }

  if (!stats) {
    return <EmptyState message="No statistics available for this device." />;
  }

  const formatNumber = (num: number) => num.toFixed(2);

  return (
    <div className="max-w-6xl mx-auto">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        {/* Voltage */}
        <div className="bg-white dark:bg-zinc-900 rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Voltage</h2>
          <div className="space-y-2">
            <Row label="Min" value={`${formatNumber(stats.voltage.min)} V`} />
            <Row label="Max" value={`${formatNumber(stats.voltage.max)} V`} />
            <Row label="Avg" value={`${formatNumber(stats.voltage.avg)} V`} />
          </div>
        </div>

        {/* Current */}
        <div className="bg-white dark:bg-zinc-900 rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Current</h2>
          <div className="space-y-2">
            <Row label="Min" value={`${formatNumber(stats.current.min)} A`} />
            <Row label="Max" value={`${formatNumber(stats.current.max)} A`} />
            <Row label="Avg" value={`${formatNumber(stats.current.avg)} A`} />
          </div>
        </div>

        {/* Power */}
        <div className="bg-white dark:bg-zinc-900 rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Power</h2>
          <div className="space-y-2">
            <Row label="Min" value={`${formatNumber(stats.power.min)} W`} />
            <Row label="Max" value={`${formatNumber(stats.power.max)} W`} />
            <Row label="Avg" value={`${formatNumber(stats.power.avg)} W`} />
            <div className="pt-2 border-t border-zinc-200 dark:border-zinc-700">
              <Row
                label="Total"
                value={`${formatNumber(stats.power.total)} Wh`}
              />
            </div>
          </div>
        </div>

        {/* Temperature */}
        <div className="bg-white dark:bg-zinc-900 rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Temperature</h2>
          <div className="space-y-2">
            <Row
              label="Min"
              value={`${formatNumber(stats.temperature.min)} °C`}
            />
            <Row
              label="Max"
              value={`${formatNumber(stats.temperature.max)} °C`}
            />
            <Row
              label="Avg"
              value={`${formatNumber(stats.temperature.avg)} °C`}
            />
          </div>
        </div>

        {/* Data points */}
        <div className="bg-white dark:bg-zinc-900 rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Data Points</h2>
          <div className="text-3xl font-bold">
            {stats.data_points.toLocaleString()}
          </div>
        </div>

        {/* Time range */}
        <div className="bg-white dark:bg-zinc-900 rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Time Range</h2>
          <div className="space-y-2">
            <div>
              <div className="text-sm text-zinc-500">Start</div>
              <div>{new Date(stats.start_time).toLocaleString()}</div>
            </div>
            <div>
              <div className="text-sm text-zinc-500">End</div>
              <div>{new Date(stats.end_time).toLocaleString()}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-zinc-500">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}
