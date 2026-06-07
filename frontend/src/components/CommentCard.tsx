import type { CommentResponse } from "../types";

interface CommentCardProps {
  comment: CommentResponse;
}

function highlightTriggerWords(text: string, triggerWords: string[]): JSX.Element {
  if (!triggerWords || triggerWords.length === 0) {
    return <span>{text}</span>;
  }

  // Create a regex that matches any trigger word (case-insensitive)
  const pattern = triggerWords
    .map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"))
    .join("|");
  const regex = new RegExp(`(${pattern})`, "gi");
  const parts = text.split(regex);

  return (
    <span>
      {parts.map((part, i) => {
        const isMatch = triggerWords.some(
          (w) => w.toLowerCase() === part.toLowerCase()
        );
        return isMatch ? (
          <mark key={i} className="bg-red-200 text-red-900 px-0.5 rounded">
            {part}
          </mark>
        ) : (
          <span key={i}>{part}</span>
        );
      })}
    </span>
  );
}

function CommentCard({ comment }: CommentCardProps) {
  const scorePercent = Math.round(comment.toxicity_score * 100);

  return (
    <div
      className={`p-4 rounded-lg border ${
        comment.is_toxic
          ? "bg-red-50 border-red-200"
          : "bg-white border-gray-200"
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          {/* Section badge */}
          {comment.section_title && (
            <span className="inline-block text-xs font-medium text-blue-700 bg-blue-100 px-2 py-0.5 rounded mb-2">
              {comment.section_title}
            </span>
          )}

          {/* Comment text with highlighted trigger words */}
          <p className="text-sm text-gray-800 leading-relaxed">
            {highlightTriggerWords(comment.text, comment.trigger_words)}
          </p>

          {/* Author and timestamp */}
          <div className="mt-2 flex items-center gap-3 text-xs text-gray-500">
            {comment.author && <span className="font-medium">{comment.author}</span>}
            {comment.timestamp && <span>{comment.timestamp}</span>}
          </div>
        </div>

        {/* Toxicity score bar */}
        <div className="flex-shrink-0 w-20 text-right">
          <span
            className={`text-sm font-bold ${
              comment.is_toxic ? "text-red-600" : "text-green-600"
            }`}
          >
            {scorePercent}%
          </span>
          <div className="mt-1 w-full h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${
                comment.is_toxic ? "bg-red-500" : "bg-green-500"
              }`}
              style={{ width: `${scorePercent}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export default CommentCard;
