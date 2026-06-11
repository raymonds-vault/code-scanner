import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { listScans, type ScanSummary } from "../api/scans.ts";
import Navbar from "../components/Navbar.tsx";

const statusColour: Record<string, string> = {
  pending: "bg-neutral-100 text-neutral-600",
  running: "bg-blue-100 text-blue-700",
  completed: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
};

function formatDate(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function Dashboard() {
  const [scans, setScans] = useState<ScanSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    listScans()
      .then((res) => {
        setScans(res.scans);
        setTotal(res.total);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex min-h-screen">
      <Navbar />
      <main className="flex-1 p-8">
        <div className="max-w-5xl mx-auto">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-semibold text-neutral-900">My Scans</h1>
              <p className="text-sm text-neutral-500 mt-0.5">{total} total scan{total !== 1 ? "s" : ""}</p>
            </div>
          </div>

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

          {!loading && !error && scans.length === 0 && (
            <div className="text-center py-20 text-neutral-400">
              <p className="text-4xl mb-3">🔍</p>
              <p className="text-sm">No scans yet. Submit code via the CLI or API to get started.</p>
            </div>
          )}

          {!loading && scans.length > 0 && (
            <div className="bg-white rounded-xl border border-neutral-200 divide-y divide-neutral-100 overflow-hidden">
              {scans.map((scan) => (
                <button
                  key={scan.id}
                  onClick={() => navigate(`/scans/${scan.id}`)}
                  className="w-full text-left px-6 py-4 hover:bg-neutral-50 transition-colors flex items-center gap-4"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium capitalize ${
                          statusColour[scan.status] ?? "bg-neutral-100 text-neutral-600"
                        }`}
                      >
                        {scan.status}
                      </span>
                      {scan.status === "running" && (
                        <span className="text-xs text-blue-600">
                          {Math.round(scan.progress * 100)}%
                        </span>
                      )}
                    </div>
                    <p className="text-sm font-mono text-neutral-500 truncate">
                      {scan.id}
                    </p>
                    {scan.metadata.repo_root != null && (
                      <p className="text-xs text-neutral-400 truncate mt-0.5">
                        {String(scan.metadata.repo_root)}
                      </p>
                    )}
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-sm font-semibold text-neutral-900">
                      {scan.finding_count}{" "}
                      <span className="font-normal text-neutral-500">
                        finding{scan.finding_count !== 1 ? "s" : ""}
                      </span>
                    </p>
                    <p className="text-xs text-neutral-400 mt-0.5">{formatDate(scan.created_at)}</p>
                  </div>
                  <span className="text-neutral-300 ml-1">›</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
