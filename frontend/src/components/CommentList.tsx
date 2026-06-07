import { useState, useMemo } from "react";
import type { CommentResponse } from "../types";
import CommentCard from "./CommentCard";

interface CommentListProps {
  comments: CommentResponse[];
}

type SortMode = "toxicity" | "chronological";
type FilterMode = "all" | "toxic" | "clean";

function CommentList({ comments }: CommentListProps) {
  const [sortMode, setSortMode] = useState<SortMode>("toxicity");
  const [filterMode, setFilterMode] = useState<FilterMode>("all");
  const [collapsedSections, setCollapsedSections] = useState<Set<string>>(
    new Set()
  );

  const filteredComments = useMemo(() => {
    let result = [...comments];

    // Filter
    if (filterMode === "toxic") {
      result = result.filter((c) => c.is_toxic);
    } else if (filterMode === "clean") {
      result = result.filter((c) => !c.is_toxic);
    }

    // Sort
    if (sortMode === "toxicity") {
      result.sort((a, b) => b.toxicity_score - a.toxicity_score);
    }

    return result;
  }, [comments, sortMode, filterMode]);

  // Group by section
  const groupedComments = useMemo(() => {
    const groups: Record<string, CommentResponse[]> = {};
    for (const comment of filteredComments) {
      const section = comment.section_title || "General";
      if (!groups[section]) {
        groups[section] = [];
      }
      groups[section].push(comment);
    }
    return groups;
  }, [filteredComments]);

  const toggleSection = (section: string) => {
    setCollapsedSections((prev) => {
      const next = new Set(prev);
      if (next.has(section)) {
        next.delete(section);
      } else {
        next.add(section);
      }
      return next;
    });
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-800">
          Comments ({filteredComments.length})
        </h3>

        <div className="flex gap-3">
          {/* Sort controls */}
          <select
            value={sortMode}
            onChange={(e) => setSortMode(e.target.value as SortMode)}
            className="text-sm border rounded-md px-2 py-1"
          >
            <option value="toxicity">Sort by Toxicity</option>
            <option value="chronological">Chronological</option>
          </select>

          {/* Filter controls */}
          <select
            value={filterMode}
            onChange={(e) => setFilterMode(e.target.value as FilterMode)}
            className="text-sm border rounded-md px-2 py-1"
          >
            <option value="all">All Comments</option>
            <option value="toxic">Toxic Only</option>
            <option value="clean">Clean Only</option>
          </select>
        </div>
      </div>

      {/* Grouped by section */}
      <div className="space-y-6">
        {Object.entries(groupedComments).map(([section, sectionComments]) => (
          <div key={section}>
            <button
              onClick={() => toggleSection(section)}
              className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-blue-600 mb-2"
            >
              <span className="text-xs">
                {collapsedSections.has(section) ? "+" : "-"}
              </span>
              {section} ({sectionComments.length})
            </button>

            {!collapsedSections.has(section) && (
              <div className="space-y-3 ml-4">
                {sectionComments.map((comment) => (
                  <CommentCard key={comment.id} comment={comment} />
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {filteredComments.length === 0 && (
        <p className="text-gray-500 text-center py-8">
          No comments match the current filter.
        </p>
      )}
    </div>
  );
}

export default CommentList;
