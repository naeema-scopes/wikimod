import { useMemo } from "react";
import type { CommentResponse } from "../types";

interface ComparisonViewProps {
  comments: CommentResponse[];
}

interface SectionSummary {
  title: string;
  avgScore: number;
  commentCount: number;
  toxicCount: number;
  sampleComments: CommentResponse[];
}

function ComparisonView({ comments }: ComparisonViewProps) {
  const { healthiest, mostHeated } = useMemo(() => {
    // Group by section
    const sections: Record<string, CommentResponse[]> = {};
    for (const c of comments) {
      const section = c.section_title || "General";
      if (!sections[section]) sections[section] = [];
      sections[section].push(c);
    }

    // Calculate section summaries (min 2 comments to be meaningful)
    const summaries: SectionSummary[] = Object.entries(sections)
      .filter(([_, cs]) => cs.length >= 2)
      .map(([title, cs]) => {
        const avgScore =
          cs.reduce((sum, c) => sum + c.toxicity_score, 0) / cs.length;
        const toxicCount = cs.filter((c) => c.is_toxic).length;
        return {
          title,
          avgScore,
          commentCount: cs.length,
          toxicCount,
          sampleComments: cs.slice(0, 3),
        };
      });

    if (summaries.length < 2) {
      return { healthiest: null, mostHeated: null };
    }

    summaries.sort((a, b) => a.avgScore - b.avgScore);

    return {
      healthiest: summaries[0],
      mostHeated: summaries[summaries.length - 1],
    };
  }, [comments]);

  if (!healthiest || !mostHeated || healthiest.title === mostHeated.title) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">
        Section Comparison
      </h3>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Healthiest section */}
        <div className="border border-green-200 bg-green-50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-green-600 text-lg">&#9679;</span>
            <h4 className="font-medium text-green-800">
              Healthiest: {healthiest.title}
            </h4>
          </div>
          <div className="text-sm text-green-700 mb-3">
            <p>Avg toxicity: {(healthiest.avgScore * 100).toFixed(1)}%</p>
            <p>
              {healthiest.commentCount} comments, {healthiest.toxicCount} toxic
            </p>
          </div>
          <div className="space-y-2">
            {healthiest.sampleComments.map((c) => (
              <p
                key={c.id}
                className="text-xs text-gray-600 bg-white rounded p-2 truncate"
              >
                <span className="font-medium">{c.author || "Anon"}:</span>{" "}
                {c.text}
              </p>
            ))}
          </div>
        </div>

        {/* Most heated section */}
        <div className="border border-red-200 bg-red-50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-red-600 text-lg">&#9679;</span>
            <h4 className="font-medium text-red-800">
              Most Heated: {mostHeated.title}
            </h4>
          </div>
          <div className="text-sm text-red-700 mb-3">
            <p>Avg toxicity: {(mostHeated.avgScore * 100).toFixed(1)}%</p>
            <p>
              {mostHeated.commentCount} comments, {mostHeated.toxicCount} toxic
            </p>
          </div>
          <div className="space-y-2">
            {mostHeated.sampleComments.map((c) => (
              <p
                key={c.id}
                className="text-xs text-gray-600 bg-white rounded p-2 truncate"
              >
                <span className="font-medium">{c.author || "Anon"}:</span>{" "}
                {c.text}
              </p>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default ComparisonView;
