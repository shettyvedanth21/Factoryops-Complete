// "use client";

// import { useEffect, useState, useRef, useCallback } from "react";
// import { useParams } from "next/navigation";
// import { getTelemetry } from "@/lib/dataApi";
// import { ApiError } from "@/components/ApiError";
// import { EmptyState } from "@/components/EmptyState";

// interface TelemetryData {
//   timestamp: string;
//   voltage: number;
//   current: number;
//   power: number;
//   temperature: number;
// }

// export default function TelemetryPage() {
//   const params = useParams();
//   const deviceId = params.deviceId as string;

//   const [data, setData] = useState<TelemetryData[]>([]);
//   const [loading, setLoading] = useState(true);
//   const [error, setError] = useState<string | null>(null);
//   const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
//   const intervalRef = useRef<NodeJS.Timeout | null>(null);

//   const fetchTelemetry = useCallback(async (isRefresh = false) => {
//     if (!isRefresh) {
//       setLoading(true);
//     }
//     setError(null);

//     try {
//       const result = await getTelemetry(deviceId, {
//         limit: "20",
//       });

//       const rows = Array.isArray(result)
//         ? result
//         : result?.data ?? [];

//       setData(rows);
//       setLastUpdated(new Date());
//     } catch (err) {
//       setError(
//         err instanceof Error
//           ? err.message
//           : "Failed to fetch telemetry data"
//       );
//     } finally {
//       if (!isRefresh) {
//         setLoading(false);
//       }
//     }
//   }, [deviceId]);

//   useEffect(() => {
//     if (!deviceId) return;

//     // Initial fetch
//     fetchTelemetry(false);

//     // Set up auto-refresh every 5 seconds
//     intervalRef.current = setInterval(() => {
//       fetchTelemetry(true);
//     }, 5000);

//     // Clear interval on unmount
//     return () => {
//       if (intervalRef.current) {
//         clearInterval(intervalRef.current);
//       }
//     };
//   }, [deviceId, fetchTelemetry]);

//   if (loading) {
//     return (
//       <div className="flex items-center justify-center h-64">
//         <div className="text-center">
//           <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-zinc-900 dark:border-zinc-50 mx-auto"></div>
//           <p className="mt-4 text-zinc-600 dark:text-zinc-400">
//             Loading telemetry data...
//           </p>
//         </div>
//       </div>
//     );
//   }

//   if (error) {
//     return <ApiError message={error} />;
//   }

//   return (
//     <div className="bg-white dark:bg-zinc-900 rounded-lg shadow overflow-hidden">
//       <div className="px-6 py-4 border-b border-zinc-200 dark:border-zinc-700 flex items-center justify-between">
//         <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
//           Latest Telemetry Data
//         </h2>
//         {lastUpdated && (
//           <span className="text-sm text-zinc-500 dark:text-zinc-400">
//             Last updated: {lastUpdated.toLocaleTimeString()}
//           </span>
//         )}
//       </div>

//       <table className="w-full">
//         <thead className="bg-zinc-100 dark:bg-zinc-800">
//           <tr>
//             <th className="px-6 py-3 text-left text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">
//               Timestamp
//             </th>
//             <th className="px-6 py-3 text-left text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">
//               Voltage
//             </th>
//             <th className="px-6 py-3 text-left text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">
//               Current
//             </th>
//             <th className="px-6 py-3 text-left text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">
//               Power
//             </th>
//             <th className="px-6 py-3 text-left text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">
//               Temperature
//             </th>
//           </tr>
//         </thead>

//         <tbody className="divide-y divide-zinc-200 dark:divide-zinc-700">
//           {data.length === 0 ? (
//             <tr>
//               <td
//                 colSpan={5}
//                 className="px-6 py-8"
//               >
//                 <EmptyState message="No telemetry data available" />
//               </td>
//             </tr>
//           ) : (
//             data.map((row, index) => (
//               <tr
//                 key={index}
//                 className="hover:bg-zinc-50 dark:hover:bg-zinc-800/50"
//               >
//                 <td className="px-6 py-4 whitespace-nowrap text-sm text-zinc-900 dark:text-zinc-100">
//                   {new Date(row.timestamp).toLocaleString()}
//                 </td>
//                 <td className="px-6 py-4 whitespace-nowrap text-sm text-zinc-900 dark:text-zinc-100">
//                   {row.voltage} V
//                 </td>
//                 <td className="px-6 py-4 whitespace-nowrap text-sm text-zinc-900 dark:text-zinc-100">
//                   {row.current} A
//                 </td>
//                 <td className="px-6 py-4 whitespace-nowrap text-sm text-zinc-900 dark:text-zinc-100">
//                   {row.power} W
//                 </td>
//                 <td className="px-6 py-4 whitespace-nowrap text-sm text-zinc-900 dark:text-zinc-100">
//                   {row.temperature} °C
//                 </td>
//               </tr>
//             ))
//           )}
//         </tbody>
//       </table>
//     </div>
//   );
// }



"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useParams } from "next/navigation";

import {
  getTelemetry,
  getDeviceStats,
  getDeviceAlerts,
  Alert,
} from "@/lib/dataApi";

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

interface DeviceStats {
  voltage?: { min: number; max: number; avg: number };
  current?: { min: number; max: number; avg: number };
  power?: { min: number; max: number; avg: number };
  temperature?: { min: number; max: number; avg: number };
}

export default function TelemetryPage() {
  const params = useParams();
  const deviceId = params.deviceId as string;

  const [telemetry, setTelemetry] = useState<TelemetryData[]>([]);
  const [stats, setStats] = useState<DeviceStats | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchAll = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);

    try {
      const [telemetryRes, statsRes, alertsRes] = await Promise.all([
        getTelemetry(deviceId, { limit: "200" }),
        getDeviceStats(deviceId),
        getDeviceAlerts(deviceId, { page: 1, pageSize: 5 }),
      ]);

      const rows = Array.isArray(telemetryRes)
        ? telemetryRes
        : telemetryRes?.data ?? [];

      setTelemetry(rows);
      setStats(statsRes ?? null);
      setAlerts(alertsRes.data ?? []);
      setLastUpdated(new Date());
      setError(null);
    } catch (e: any) {
      setError(e?.message || "Failed to load telemetry dashboard");
    } finally {
      if (!silent) setLoading(false);
    }
  }, [deviceId]);

  useEffect(() => {
    if (!deviceId) return;

    fetchAll(false);

    intervalRef.current = setInterval(() => {
      fetchAll(true);
    }, 5000);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [deviceId, fetchAll]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-zinc-900" />
      </div>
    );
  }

  if (error) {
    return <ApiError message={error} />;
  }

  const chartData = [...telemetry]
    .slice()
    .reverse()
    .map((t) => ({
      ...t,
      ts: new Date(t.timestamp).getTime(),
    }));

  return (
    <div className="space-y-6">

      {/* header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">
          Device {deviceId} – Live telemetry
        </h2>

        {lastUpdated && (
          <span className="text-sm text-zinc-500">
            Updated {lastUpdated.toLocaleTimeString()}
          </span>
        )}
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">

        <KpiCard
          title="Power (avg)"
          value={stats?.power?.avg}
          unit="W"
        />

        <KpiCard
          title="Voltage (avg)"
          value={stats?.voltage?.avg}
          unit="V"
        />

        <KpiCard
          title="Current (avg)"
          value={stats?.current?.avg}
          unit="A"
        />

        <KpiCard
          title="Temperature (avg)"
          value={stats?.temperature?.avg}
          unit="°C"
        />

      </div>

      {/* live chart */}
      <div className="border rounded p-4">
        <h3 className="font-medium mb-3">
          Power – last samples
        </h3>

        {chartData.length === 0 ? (
          <EmptyState message="No telemetry data available" />
        ) : (
          <div style={{ height: 320 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="ts"
                  type="number"
                  domain={["dataMin", "dataMax"]}
                  tickFormatter={(v) =>
                    new Date(v).toLocaleTimeString()
                  }
                />
                <YAxis />
                <Tooltip
                  labelFormatter={(v) =>
                    new Date(Number(v)).toLocaleString()
                  }
                />
                <Line
                  type="monotone"
                  dataKey="power"
                  stroke="#2563eb"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* alerts */}
      <div className="border rounded p-4">
        <h3 className="font-medium mb-3">
          Recent alerts
        </h3>

        {alerts.length === 0 ? (
          <div className="text-sm text-zinc-500">
            No active alerts
          </div>
        ) : (
          <div className="space-y-2">
            {alerts.map((a) => (
              <div
                key={a.alertId}
                className="flex justify-between items-start rounded border px-3 py-2"
              >
                <div>
                  <div className="text-sm font-medium">
                    {a.message}
                  </div>
                  <div className="text-xs text-zinc-500">
                    {new Date(a.createdAt).toLocaleString()}
                  </div>
                </div>

                <span className="text-xs rounded px-2 py-0.5 bg-zinc-200">
                  {a.severity}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* raw telemetry table */}
      <div className="border rounded overflow-hidden">

        <div className="px-4 py-2 border-b font-medium">
          Latest samples
        </div>

        <table className="w-full text-sm">
          <thead className="bg-zinc-100">
            <tr>
              <th className="px-3 py-2 text-left">Time</th>
              <th className="px-3 py-2 text-left">Voltage</th>
              <th className="px-3 py-2 text-left">Current</th>
              <th className="px-3 py-2 text-left">Power</th>
              <th className="px-3 py-2 text-left">Temp</th>
            </tr>
          </thead>

          <tbody>
            {telemetry.length === 0 ? (
              <tr>
                <td colSpan={5} className="p-4">
                  <EmptyState message="No telemetry data" />
                </td>
              </tr>
            ) : (
              telemetry.map((r, i) => (
                <tr key={i} className="border-t">
                  <td className="px-3 py-2">
                    {new Date(r.timestamp).toLocaleString()}
                  </td>
                  <td className="px-3 py-2">{r.voltage}</td>
                  <td className="px-3 py-2">{r.current}</td>
                  <td className="px-3 py-2">{r.power}</td>
                  <td className="px-3 py-2">{r.temperature}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function KpiCard({
  title,
  value,
  unit,
}: {
  title: string;
  value?: number;
  unit?: string;
}) {
  return (
    <div className="border rounded p-4">
      <div className="text-sm text-zinc-500 mb-1">
        {title}
      </div>
      <div className="text-xl font-semibold">
        {value !== undefined && value !== null
          ? value.toFixed(2)
          : "--"}{" "}
        <span className="text-sm font-normal">
          {unit}
        </span>
      </div>
    </div>
  );
}