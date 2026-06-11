import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getScan, type Finding, type ScanDetail } from "../api/scans.ts";
import Navbar from "../components/Navbar.tsx";
import SeverityBadge from "../components/SeverityBadge.tsx";

const sourceLabel: Record<string, string> = {
  static: "Static",
  llm: "LLM",
  hybrid: "Hybrid",
};

export default function ScanDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [scan, setScan] = useState<ScanDetail | null>(null);
  const [selected, setSelected] = useState<Finding | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    getScan(id)
      .then(setScan)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  const highCount = scan?.findings.filter((f) => f.severity === "high").length ?? 0;
  const medCount = scan?.findings.filter((f) => f.severity === "medium").length ?? 0;
  const lowCount = scan?.findings.filter((f) => f.severity === "low").length ?? 0;

  return (
    <div className="flex min-h-screen">
      <Navbar />
      <main className="flex-1 p-8 overflow-auto">
        <div className="max-w-5xl mx-auto">
          <button
            onClick={() => navigate("/dashboard")}
            className="text-sm text-neutral-500 hover:text-neutral-900 mb-4 flex items-center gap-1"
          >
            ← Back to scans
          </button>

          {loading && (
            <div className="flex items-center justify-center py-20">
              <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
            </div>
          )}

          {error && (
            <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-sm text-red-700">
              {error}
            </div>
          )}

          {scan && (
            <>
              <div className="bg-white rounded-xl border border-neutral-200 p-6 mb-6">
                <div className="flex items-start justify-between gap-4 flex-wrap">
                  <div>
                    <h1 className="text-lg font-semibold text-neutral-900 mb-1">Scan detail</h1>
                    <p className="text-sm font-mono text-neutral-500">{scan.id}</p>
                  </div>
                  <span
                    className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium capitalize ${
                      scan.status === "completed"
                        ? "bg-green-100 text-green-700"
                        : scan.status === "running"
                        ? "bg-blue-100 text-blue-700"
                        : scan.status === "failed"
                        ? "bg-red-100 text-red-700"
                        : "bg-neutral-100 text-neutral-600"
                    }`}
                  >
                    {scan.status}
                  </span>
                </div>

                <div className="mt-4 flex gap-6 text-sm">
                  <div>
                    <p className="text-neutral-400 text-xs mb-0.5">High</p>
                    <p className="text-red-600 font-semibold text-lg">{highCount}</p>
                  </div>
                  <div>
                    <p className="text-neutral-400 text-xs mb-0.5">Medium</p>
                    <p className="text-orange-500 font-semibold text-lg">{medCount}</p>
                  </div>
                  <div>
                    <p className="text-neutral-400 text-xs mb-0.5">Low</p>
                    <p className="text-yellow-500 font-semibold text-lg">{lowCount}</p>
                  </div>
                  <div>
                    <p className="text-neutral-400 text-xs mb-0.5">Total</p>
                    <p className="text-neutral-900 font-semibold text-lg">{scan.findings.length}</p>
                  </div>
                </div>
              </div>

              {scan.findings.length === 0 ? (
                <div className="text-center py-16 text-neutral-400">
                  <p className="text-3xl mb-2">✅</p>
                  <p className="text-sm">No findings detected in this scan.</p>
                </div>
              ) : (
                <div className="flex gap-4">
                  <div className="flex-1 bg-white rounded-xl border border-neutral-200 divide-y divide-neutral-100 overflow-hidden">
                    {scan.findings.map((f) => (
                      <button
                        key={f.id}
                        onClick={() => setSelected(f)}
                        className={`w-full text-left px-5 py-3.5 hover:bg-neutral-50 transition-colors ${
                          selected?.id === f.id ? "bg-blue-50" : ""
                        }`}
                      >
                        <div className="flex items-center gap-2 mb-1 flex-wrap">
                          <SeverityBadge severity={f.severity} />
                          <span className="text-xs text-neutral-500 bg-neutral-100 px-1.5 py-0.5 rounded">
                            {sourceLabel[f.source] ?? f.source}
                          </span>
                          <span className="text-xs text-neutral-400">
                            {Math.round(f.confidence * 100)}% confidence
                          </span>
                        </div>
                        <p className="text-sm font-medium text-neutral-900 capitalize">
                          {f.vulnerability_type.replace(/_/g, " ")}
                        </p>
                        <p className="text-xs text-neutral-400 font-mono truncate mt-0.5">
                          {f.file_path}:{f.line_number}
                        </p>
                      </button>
                    ))}
                  </div>

                  {selected && (
                    <div className="w-80 shrink-0 bg-white rounded-xl border border-neutral-200 p-5 self-start sticky top-8">
                      <div className="flex items-center justify-between mb-3">
                        <SeverityBadge severity={selected.severity} />
                        <button
                          onClick={() => setSelected(null)}
                          className="text-neutral-400 hover:text-neutral-700 text-lg leading-none"
                        >
                          ×
                        </button>
                      </div>
                      <h3 className="text-sm font-semibold text-neutral-900 capitalize mb-1">
                        {selected.vulnerability_type.replace(/_/g, " ")}
                      </h3>
                      <p className="text-xs font-mono text-neutral-500 mb-4">
                        {selected.file_path}:{selected.line_number}
                      </p>
                      {selected.explanation && (
                        <div className="mb-4">
                          <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-1">
                            Explanation
                          </p>
                          <p className="text-sm text-neutral-700 leading-relaxed">
                            {selected.explanation}
                          </p>
                        </div>
                      )}
                      {selected.fix && (
                        <div>
                          <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-1">
                            Suggested fix
                          </p>
                          <pre className="text-xs bg-neutral-50 border border-neutral-200 rounded-lg p-3 whitespace-pre-wrap text-neutral-700 leading-relaxed">
                            {selected.fix}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}
