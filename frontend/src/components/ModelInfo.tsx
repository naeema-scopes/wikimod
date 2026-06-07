import { useState, useEffect } from "react";
import type { ModelMetrics, ModelLimitations } from "../types";
import { getModelMetrics, getModelLimitations } from "../api/client";

function ModelInfo() {
  const [metrics, setMetrics] = useState<ModelMetrics | null>(null);
  const [limitations, setLimitations] = useState<ModelLimitations | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [m, l] = await Promise.all([
          getModelMetrics(),
          getModelLimitations(),
        ]);
        setMetrics(m);
        setLimitations(l);
      } catch (err) {
        // Silently fail for demo
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="text-center py-12 text-gray-500">
        Loading model information...
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Metrics Section */}
      {metrics && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Model Performance</h2>

          {metrics.note && (
            <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded text-sm text-yellow-800">
              {metrics.note}
            </div>
          )}

          <div className="grid md:grid-cols-2 gap-6">
            {/* Per-class metrics */}
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-3">
                Per-Class Metrics
              </h3>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-gray-500">
                    <th className="pb-2 pr-4">Class</th>
                    <th className="pb-2 pr-4">Precision</th>
                    <th className="pb-2 pr-4">Recall</th>
                    <th className="pb-2">F1</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b">
                    <td className="py-2 pr-4 font-medium text-green-700">
                      Clean
                    </td>
                    <td className="py-2 pr-4">
                      {(metrics.precision_clean * 100).toFixed(1)}%
                    </td>
                    <td className="py-2 pr-4">
                      {(metrics.recall_clean * 100).toFixed(1)}%
                    </td>
                    <td className="py-2">
                      {(metrics.f1_clean * 100).toFixed(1)}%
                    </td>
                  </tr>
                  <tr className="border-b">
                    <td className="py-2 pr-4 font-medium text-red-700">
                      Toxic
                    </td>
                    <td className="py-2 pr-4">
                      {(metrics.precision_toxic * 100).toFixed(1)}%
                    </td>
                    <td className="py-2 pr-4">
                      {(metrics.recall_toxic * 100).toFixed(1)}%
                    </td>
                    <td className="py-2">
                      {(metrics.f1_toxic * 100).toFixed(1)}%
                    </td>
                  </tr>
                </tbody>
              </table>

              <div className="mt-4 space-y-1 text-sm text-gray-600">
                <p>
                  <span className="font-medium">Accuracy:</span>{" "}
                  {(metrics.accuracy * 100).toFixed(1)}%
                </p>
                <p>
                  <span className="font-medium">Weighted F1:</span>{" "}
                  {(metrics.weighted_f1 * 100).toFixed(1)}%
                </p>
                <p>
                  <span className="font-medium">Training samples:</span>{" "}
                  {metrics.training_samples.toLocaleString()}
                </p>
              </div>
            </div>

            {/* Confusion matrix */}
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-3">
                Confusion Matrix
              </h3>
              {metrics.confusion_matrix &&
                metrics.confusion_matrix.length === 2 && (
                  <div className="inline-block">
                    <table className="text-sm border-collapse">
                      <thead>
                        <tr>
                          <th className="p-2"></th>
                          <th className="p-2 text-center text-gray-500 text-xs">
                            Pred. Clean
                          </th>
                          <th className="p-2 text-center text-gray-500 text-xs">
                            Pred. Toxic
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td className="p-2 text-xs text-gray-500 font-medium">
                            Actual Clean
                          </td>
                          <td className="p-2 text-center bg-green-100 border font-bold text-green-800">
                            {metrics.confusion_matrix[0][0]}
                          </td>
                          <td className="p-2 text-center bg-red-50 border text-red-600">
                            {metrics.confusion_matrix[0][1]}
                          </td>
                        </tr>
                        <tr>
                          <td className="p-2 text-xs text-gray-500 font-medium">
                            Actual Toxic
                          </td>
                          <td className="p-2 text-center bg-red-50 border text-red-600">
                            {metrics.confusion_matrix[1][0]}
                          </td>
                          <td className="p-2 text-center bg-green-100 border font-bold text-green-800">
                            {metrics.confusion_matrix[1][1]}
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                )}
            </div>
          </div>
        </div>
      )}

      {/* Limitations Section */}
      {limitations && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">
            Known Limitations &amp; Biases
          </h2>
          <p className="text-sm text-gray-600 mb-4">
            This model has important limitations that users should understand.
            Health scores should be treated as signals for human review, not
            automated moderation decisions.
          </p>

          <ul className="space-y-3">
            {limitations.limitations.map((limitation, i) => (
              <li key={i} className="flex gap-3 text-sm text-gray-700">
                <span className="text-yellow-500 flex-shrink-0 mt-0.5">
                  &#9888;
                </span>
                <span>{limitation}</span>
              </li>
            ))}
          </ul>

          {limitations.references.length > 0 && (
            <div className="mt-6 pt-4 border-t">
              <h3 className="text-sm font-medium text-gray-500 mb-2">
                References
              </h3>
              <ul className="space-y-1 text-sm text-gray-600">
                {limitations.references.map((ref, i) => (
                  <li key={i}>{ref}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default ModelInfo;
