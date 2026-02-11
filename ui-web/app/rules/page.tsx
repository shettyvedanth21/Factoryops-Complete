"use client";

import { useEffect, useState } from "react";
import { listRules, Rule, updateRuleStatus, deleteRule } from "@/lib/ruleApi";
import { ApiError } from "@/components/ApiError";
import { EmptyState } from "@/components/EmptyState";

export default function RulesPage() {
  const [rules, setRules] = useState<Rule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await listRules();
      setRules(result.data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load rules");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const toggleRule = async (rule: Rule) => {
    const newStatus = rule.status === "active" ? "paused" : "active";
    await updateRuleStatus(rule.ruleId, newStatus);
    await load();
  };

  const removeRule = async (ruleId: string) => {
    await deleteRule(ruleId);
    await load();
  };

  if (loading) return <div>Loading rules…</div>;
  if (error) return <ApiError message={error} />;
  if (rules.length === 0) return <EmptyState message="No rules created yet." />;

  return (
    <div className="bg-white dark:bg-zinc-900 rounded-lg shadow overflow-hidden">
      <div className="px-6 py-4 border-b">
        <h2 className="text-lg font-semibold">Rules</h2>
      </div>

      <table className="w-full">
        <thead>
          <tr className="text-left text-sm text-zinc-500">
            <th className="px-6 py-3">Name</th>
            <th className="px-6 py-3">Property</th>
            <th className="px-6 py-3">Condition</th>
            <th className="px-6 py-3">Threshold</th>
            <th className="px-6 py-3">Status</th>
            <th className="px-6 py-3"></th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {rules.map((r) => (
            <tr key={r.ruleId}>
              <td className="px-6 py-3">{r.ruleName}</td>
              <td className="px-6 py-3">{r.property}</td>
              <td className="px-6 py-3">{r.condition}</td>
              <td className="px-6 py-3">{r.threshold}</td>
              <td className="px-6 py-3">{r.status}</td>
              <td className="px-6 py-3 flex gap-2">
                <button
                  onClick={() => toggleRule(r)}
                  className="text-blue-600 text-sm"
                >
                  {r.status === "active" ? "Pause" : "Resume"}
                </button>
                <button
                  onClick={() => removeRule(r.ruleId)}
                  className="text-red-600 text-sm"
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}