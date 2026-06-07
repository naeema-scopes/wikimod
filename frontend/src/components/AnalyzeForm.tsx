import { useState } from "react";

function AnalyzeForm() {
  const [url, setUrl] = useState("");

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Analyze a Wikipedia Talk Page</h2>
        <p className="text-gray-600 mb-6">
          Enter a Wikipedia article URL to analyze the toxicity of its talk page discussions.
        </p>
        <div className="flex gap-3">
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://en.wikipedia.org/wiki/Article_Name"
            className="flex-1 rounded-md border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition"
            disabled={!url}
          >
            Analyze
          </button>
        </div>
      </div>
    </div>
  );
}

export default AnalyzeForm;
