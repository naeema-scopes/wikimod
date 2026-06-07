import type { HealthScoreResponse } from "../types";

interface HealthScoreProps {
  healthScore: HealthScoreResponse;
}

function getScoreColor(score: number): string {
  if (score >= 80) return "text-green-600";
  if (score >= 50) return "text-yellow-500";
  return "text-red-600";
}

function getScoreRingColor(score: number): string {
  if (score >= 80) return "stroke-green-500";
  if (score >= 50) return "stroke-yellow-500";
  return "stroke-red-500";
}

function getScoreBg(score: number): string {
  if (score >= 80) return "bg-green-50 border-green-200";
  if (score >= 50) return "bg-yellow-50 border-yellow-200";
  return "bg-red-50 border-red-200";
}

function HealthScore({ healthScore }: HealthScoreProps) {
  const { score, total_comments, toxic_count, clean_count, label } =
    healthScore;

  // SVG circle parameters for the gauge
  const radius = 60;
  const circumference = 2 * Math.PI * radius;
  const progress = (score / 100) * circumference;

  return (
    <div className={`bg-white rounded-lg shadow p-6 border ${getScoreBg(score)}`}>
      <h3 className="text-lg font-semibold mb-4 text-gray-800">
        Page Health Score
      </h3>

      <div className="flex items-center gap-8">
        {/* Circular gauge */}
        <div className="relative">
          <svg width="140" height="140" className="transform -rotate-90">
            {/* Background circle */}
            <circle
              cx="70"
              cy="70"
              r={radius}
              fill="none"
              stroke="#e5e7eb"
              strokeWidth="10"
            />
            {/* Progress circle */}
            <circle
              cx="70"
              cy="70"
              r={radius}
              fill="none"
              className={getScoreRingColor(score)}
              strokeWidth="10"
              strokeDasharray={circumference}
              strokeDashoffset={circumference - progress}
              strokeLinecap="round"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className={`text-3xl font-bold ${getScoreColor(score)}`}>
              {Math.round(score)}%
            </span>
          </div>
        </div>

        {/* Stats */}
        <div>
          <p className={`text-lg font-semibold ${getScoreColor(score)}`}>
            {label}
          </p>
          <div className="mt-3 space-y-1 text-sm text-gray-600">
            <p>
              <span className="font-medium">{total_comments}</span> total
              comments
            </p>
            <p>
              <span className="font-medium text-red-600">{toxic_count}</span>{" "}
              toxic comments
            </p>
            <p>
              <span className="font-medium text-green-600">{clean_count}</span>{" "}
              clean comments
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default HealthScore;
