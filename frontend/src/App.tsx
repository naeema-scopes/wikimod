import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import AnalyzeForm from "./components/AnalyzeForm";
import HealthScore from "./components/HealthScore";
import CommentList from "./components/CommentList";
import EscalationChart from "./components/EscalationChart";
import ComparisonView from "./components/ComparisonView";
import HistoryView from "./components/HistoryView";
import ModelInfo from "./components/ModelInfo";
import { useAnalysis } from "./hooks/useAnalysis";

function Dashboard() {
  const { analysis, loading, error, submitUrl, reset } = useAnalysis();

  return (
    <div>
      <AnalyzeForm onSubmit={submitUrl} loading={loading} error={error} />

      {analysis && (
        <div className="mt-8 space-y-8">
          <HealthScore healthScore={analysis.health_score} />

          {analysis.escalation && analysis.escalation.sections.length > 0 && (
            <EscalationChart escalation={analysis.escalation} />
          )}

          <ComparisonView comments={analysis.comments} />

          <CommentList comments={analysis.comments} />
        </div>
      )}
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
            <div>
              <Link to="/" className="text-2xl font-bold text-gray-900 hover:text-blue-600">
                WikiMod
              </Link>
              <p className="text-sm text-gray-500">
                Wikipedia Talk Page Toxicity Monitor
              </p>
            </div>
            <nav className="flex gap-4 text-sm">
              <Link to="/" className="text-gray-600 hover:text-blue-600">
                Analyze
              </Link>
              <Link to="/history" className="text-gray-600 hover:text-blue-600">
                History
              </Link>
              <Link to="/model" className="text-gray-600 hover:text-blue-600">
                Model Info
              </Link>
            </nav>
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/history" element={<HistoryView />} />
            <Route path="/model" element={<ModelInfo />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
