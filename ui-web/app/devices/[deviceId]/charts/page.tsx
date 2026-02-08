"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { getTelemetry } from "@/lib/dataApi";
import { ApiError } from "@/components/ApiError";
import { EmptyState } from "@/components/EmptyState";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface TelemetryData {
  timestamp: string;
  voltage: number;
  current: number;
  power: number;
  temperature: number;
}

interface ChartFilters {
  start_time: string;
  end_time: string;
  aggregate: string;
  interval: string;
}

export default function ChartsPage() {
  const params = useParams();
  const deviceId = params.deviceId as string;

  const [data, setData] = useState<TelemetryData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [filters, setFilters] = useState<ChartFilters>({
    start_time: "",
    end_time: "",
    aggregate: "",
    interval: "",
  });

  const fetchTelemetry = useCallback(async () => {
    if (!deviceId) return;

    setLoading(true);
    setError(null);

    try {
      const params: Record<string, string> = {
        limit: "1000",
      };

      if (filters.start_time) params.start_time = filters.start_time;
      if (filters.end_time) params.end_time = filters.end_time;
      if (filters.aggregate) params.aggregate = filters.aggregate;
      if (filters.interval) params.interval = filters.interval;

      const result = await getTelemetry(deviceId, params);

      const telemetryData = Array.isArray(result)
        ? result
        : result?.data ?? [];

      setData(telemetryData);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to fetch telemetry data"
      );
    } finally {
      setLoading(false);
    }
  }, [deviceId, filters]);

  useEffect(() => {
    fetchTelemetry();
  }, [fetchTelemetry]);

  const handleFilterChange = (key: keyof ChartFilters, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const handleApplyFilters = () => {
    fetchTelemetry();
  };

  const handleClearFilters = () => {
    setFilters({
      start_time: "",
      end_time: "",
      aggregate: "",
      interval: "",
    });
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  const ChartCard = ({
    title,
    dataKey,
    color,
    unit,
  }: {
    title: string;
    dataKey: keyof TelemetryData;
    color: string;
    unit: string;
  }) => (
    <div className="bg-white dark:bg-zinc-900 rounded-lg shadow p-6">
      <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50 mb-4">
        {title}
      </h2>

      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.2} />
            <XAxis
              dataKey="timestamp"
              tickFormatter={formatTimestamp}
              stroke="#6B7280"
              tick={{ fill: "#6B7280", fontSize: 12 }}
            />
            <YAxis
              stroke="#6B7280"
              tick={{ fill: "#6B7280", fontSize: 12 }}
              tickFormatter={(value) => `${value} ${unit}`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#18181B",
                border: "1px solid #3F3F46",
                borderRadius: "6px",
                color: "#FAFAFA",
              }}
              labelFormatter={(label) =>
                new Date(label as string).toLocaleString()
              }
              formatter={(value: number | undefined) => [
                `${value ?? 0} ${unit}`,
                title,
              ]}
            />
            <Line
              type="monotone"
              dataKey={dataKey}
              stroke={color}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-zinc-900 dark:border-zinc-50 mx-auto"></div>
          <p className="mt-4 text-zinc-600 dark:text-zinc-400">
            Loading charts...
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return <ApiError message={error} />;
  }

  return (
    <div className="max-w-7xl mx-auto">
      {/* Filter Controls */}
      <div className="bg-white dark:bg-zinc-900 rounded-lg shadow p-6 mb-8">
        <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50 mb-4">
          Filter Options
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
              Start Time
            </label>
            <input
              type="datetime-local"
              value={filters.start_time}
              onChange={(e) =>
                handleFilterChange("start_time", e.target.value)
              }
              className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-600 rounded-md bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
              End Time
            </label>
            <input
              type="datetime-local"
              value={filters.end_time}
              onChange={(e) =>
                handleFilterChange("end_time", e.target.value)
              }
              className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-600 rounded-md bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
              Aggregate
            </label>
            <select
              value={filters.aggregate}
              onChange={(e) =>
                handleFilterChange("aggregate", e.target.value)
              }
              className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-600 rounded-md bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50"
            >
              <option value="">None</option>
              <option value="mean">Average</option>
              <option value="min">Minimum</option>
              <option value="max">Maximum</option>
              <option value="sum">Sum</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1">
              Interval
            </label>
            <select
              value={filters.interval}
              onChange={(e) =>
                handleFilterChange("interval", e.target.value)
              }
              className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-600 rounded-md bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50"
            >
              <option value="">None</option>
              <option value="1m">1 Minute</option>
              <option value="5m">5 Minutes</option>
              <option value="15m">15 Minutes</option>
              <option value="1h">1 Hour</option>
              <option value="1d">1 Day</option>
            </select>
          </div>

          <div className="flex items-end gap-2">
            <button
              onClick={handleApplyFilters}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Apply
            </button>

            <button
              onClick={handleClearFilters}
              className="flex-1 px-4 py-2 bg-zinc-200 dark:bg-zinc-700 text-zinc-700 dark:text-zinc-200 rounded-md hover:bg-zinc-300 dark:hover:bg-zinc-600"
            >
              Clear
            </button>
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      {data.length === 0 ? (
        <EmptyState message="No telemetry data available for the selected filters." />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ChartCard
            title="Voltage"
            dataKey="voltage"
            color="#10B981"
            unit="V"
          />
          <ChartCard
            title="Current"
            dataKey="current"
            color="#3B82F6"
            unit="A"
          />
          <ChartCard
            title="Power"
            dataKey="power"
            color="#F59E0B"
            unit="W"
          />
          <ChartCard
            title="Temperature"
            dataKey="temperature"
            color="#EF4444"
            unit="°C"
          />
        </div>
      )}
    </div>
  );
}
