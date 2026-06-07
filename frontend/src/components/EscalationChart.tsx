import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { EscalationReport, SectionEscalation } from "../types";

interface EscalationChartProps {
  escalation: EscalationReport;
}

const TREND_COLORS: Record<string, string> = {
  escalating: "#ef4444",
  stable: "#22c55e",
  "de-escalating": "#3b82f6",
  insufficient_data: "#9ca3af",
};

const TREND_LABELS: Record<string, string> = {
  escalating: "Escalating",
  stable: "Stable",
  "de-escalating": "De-escalating",
  insufficient_data: "Insufficient Data",
};

function SectionChart({ section }: { section: SectionEscalation }) {
  const color = TREND_COLORS[section.trend] || "#9ca3af";

  if (section.data_points.length === 0) {
    return null;
  }

  const data = section.data_points.map((dp) => ({
    index: dp.index,
    score: dp.toxicity_score,
    preview: dp.comment_preview,
    author: dp.author,
  }));

  return (
    <div className="mb-6">
      <div className="flex items-center gap-2 mb-2">
        <h4 className="text-sm font-medium text-gray-700">
          {section.section_title}
        </h4>
        <span
          className="text-xs px-2 py-0.5 rounded-full text-white"
          style={{ backgroundColor: color }}
        >
          {TREND_LABELS[section.trend]}
        </span>
        {section.trend !== "insufficient_data" && (
          <span className="text-xs text-gray-500">
            slope: {section.slope.toFixed(4)}
          </span>
        )}
      </div>

      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="index"
            label={{ value: "Comment #", position: "bottom", fontSize: 12 }}
            tick={{ fontSize: 11 }}
          />
          <YAxis
            domain={[0, 1]}
            label={{
              value: "Toxicity",
              angle: -90,
              position: "insideLeft",
              fontSize: 12,
            }}
            tick={{ fontSize: 11 }}
          />
          <Tooltip
            content={({ payload }) => {
              if (!payload || payload.length === 0) return null;
              const item = payload[0].payload;
              return (
                <div className="bg-white shadow-lg border rounded p-2 text-xs max-w-xs">
                  <p className="font-medium">
                    Score: {(item.score * 100).toFixed(1)}%
                  </p>
                  {item.author && (
                    <p className="text-gray-500">By: {item.author}</p>
                  )}
                  <p className="text-gray-600 mt-1 truncate">{item.preview}</p>
                </div>
              );
            }}
          />
          <ReferenceLine
            y={0.5}
            stroke="#f59e0b"
            strokeDasharray="5 5"
            label={{ value: "Threshold", fontSize: 10, fill: "#f59e0b" }}
          />
          <Line
            type="monotone"
            dataKey="score"
            stroke={color}
            strokeWidth={2}
            dot={{ fill: color, r: 3 }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function EscalationChart({ escalation }: EscalationChartProps) {
  const analyzableSections = escalation.sections.filter(
    (s) => s.data_points.length > 0
  );

  if (analyzableSections.length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-800">
          Conversation Escalation
        </h3>
        <span
          className="text-sm px-3 py-1 rounded-full text-white"
          style={{
            backgroundColor:
              TREND_COLORS[escalation.overall_trend] || "#9ca3af",
          }}
        >
          Overall: {TREND_LABELS[escalation.overall_trend] || "Stable"}
        </span>
      </div>

      {analyzableSections.map((section) => (
        <SectionChart key={section.section_title} section={section} />
      ))}
    </div>
  );
}

export default EscalationChart;
