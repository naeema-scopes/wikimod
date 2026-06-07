import { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { HistoryEntry } from "../types";
import { getHistory } from "../api/client";

function HistoryView() {
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchHistory() {
      try {
        const data = await getHistory();
        setHistory(data);
      } catch (err) {
        setError("Failed to load history.");
      } finally {
        setLoading(false);
      }
    }
    fetchHistory();
  }, []);

  if (loading) {
    return (
      <div className="text-center py-12 text-gray-500">Loading history...</div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12 text-red-500">{error}</div>
    );
  }

  // Group by page title for chart
  const pageGroups: Record<string, HistoryEntry[]> = {};
  for (const entry of history) {
    if (!pageGroups[entry.page_title]) {
      pageGroups[entry.page_title] = [];
    }
    pageGroups[entry.page_title].push(entry);
  }

  return (
    <div className="space-y-8">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Analysis History</h2>

        {history.length === 0 ? (
          <p className="text-gray-500 text-center py-8">
            No analyses yet. Go to the Analyze page to get started.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-gray-500">
                  <th className="pb-2 pr-4">Page</th>
                  <th className="pb-2 pr-4">Health Score</th>
                  <th className="pb-2 pr-4">Comments</th>
                  <th className="pb-2 pr-4">Toxic</th>
                  <th className="pb-2">Scanned</th>
                </tr>
              </thead>
              <tbody>
                {history.map((entry) => (
                  <tr key={entry.id} className="border-b hover:bg-gray-50">
                    <td className="py-2 pr-4 font-medium">
                      {entry.page_title}
                    </td>
                    <td className="py-2 pr-4">
                      <span
                        className={`font-bold ${
                          entry.health_score >= 80
                            ? "text-green-600"
                            : entry.health_score >= 50
                            ? "text-yellow-500"
                            : "text-red-600"
                        }`}
                      >
                        {Math.round(entry.health_score)}%
                      </span>
                    </td>
                    <td className="py-2 pr-4">{entry.total_comments}</td>
                    <td className="py-2 pr-4 text-red-600">
                      {entry.toxic_count}
                    </td>
                    <td className="py-2 text-gray-500">
                      {new Date(entry.scanned_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Health score trend charts for pages with multiple scans */}
      {Object.entries(pageGroups)
        .filter(([_, entries]) => entries.length >= 2)
        .map(([title, entries]) => {
          const chartData = [...entries]
            .reverse()
            .map((e) => ({
              date: new Date(e.scanned_at).toLocaleDateString(),
              score: e.health_score,
            }));

          return (
            <div key={title} className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">
                Health Trend: {title}
              </h3>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="score"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    dot={{ fill: "#3b82f6" }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          );
        })}
    </div>
  );
}

export default HistoryView;
