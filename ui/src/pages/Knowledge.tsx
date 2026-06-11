import { useEffect, useRef, useState } from "react";
import {
  listDocuments,
  uploadDocumentFile,
  uploadDocumentText,
  type KnowledgeDocument,
} from "../api/knowledge.ts";
import Navbar from "../components/Navbar.tsx";

type UploadMode = "text" | "file";

function formatDate(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function Knowledge() {
  const [docs, setDocs] = useState<KnowledgeDocument[]>([]);
  const [total, setTotal] = useState(0);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [docsError, setDocsError] = useState<string | null>(null);

  const [mode, setMode] = useState<UploadMode>("file");
  const [source, setSource] = useState("");
  const [category, setCategory] = useState("");
  const [docVersion, setDocVersion] = useState("1");
  const [namespace, setNamespace] = useState("");
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  function loadDocs() {
    setLoadingDocs(true);
    listDocuments()
      .then((res) => {
        setDocs(res.documents);
        setTotal(res.total);
      })
      .catch((e) => setDocsError(e.message))
      .finally(() => setLoadingDocs(false));
  }

  useEffect(() => {
    loadDocs();
  }, []);

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    setUploadError(null);
    setUploadSuccess(null);
    setUploading(true);

    try {
      let result;
      if (mode === "text") {
        result = await uploadDocumentText({
          source,
          category,
          text,
          doc_version: docVersion || "1",
          namespace: namespace || undefined,
        });
      } else {
        if (!file) throw new Error("Please select a file");
        result = await uploadDocumentFile(file, {
          source,
          category,
          doc_version: docVersion || "1",
          namespace: namespace || undefined,
        });
      }
      setUploadSuccess(
        `Ingested "${result.source}" into ${result.chunk_count} chunk${result.chunk_count !== 1 ? "s" : ""} → Pinecone (${result.namespace})`
      );
      setSource("");
      setCategory("");
      setDocVersion("1");
      setNamespace("");
      setText("");
      setFile(null);
      if (fileRef.current) fileRef.current.value = "";
      loadDocs();
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  const totalChunks = docs.reduce((s, d) => s + d.chunk_count, 0);

  return (
    <div className="flex min-h-screen">
      <Navbar />
      <main className="flex-1 p-8 overflow-auto">
        <div className="max-w-5xl mx-auto">
          <h1 className="text-2xl font-semibold text-neutral-900 mb-1">Knowledge Base</h1>
          <p className="text-sm text-neutral-500 mb-8">
            Upload security documents to augment LLM analysis via RAG.
          </p>

          <div className="grid grid-cols-3 gap-4 mb-8">
            <div className="bg-white rounded-xl border border-neutral-200 p-5">
              <p className="text-xs text-neutral-500 uppercase tracking-wide mb-1">Documents</p>
              <p className="text-3xl font-semibold text-neutral-900">{total}</p>
            </div>
            <div className="bg-white rounded-xl border border-neutral-200 p-5">
              <p className="text-xs text-neutral-500 uppercase tracking-wide mb-1">Total chunks</p>
              <p className="text-3xl font-semibold text-blue-600">{totalChunks}</p>
            </div>
            <div className="bg-white rounded-xl border border-neutral-200 p-5">
              <p className="text-xs text-neutral-500 uppercase tracking-wide mb-1">Categories</p>
              <p className="text-3xl font-semibold text-neutral-900">
                {new Set(docs.map((d) => d.category)).size}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-8">
            {/* Upload form */}
            <div>
              <h2 className="text-base font-semibold text-neutral-800 mb-4">Upload document</h2>
              <div className="bg-white rounded-xl border border-neutral-200 p-6">
                <div className="flex gap-2 mb-5">
                  {(["file", "text"] as UploadMode[]).map((m) => (
                    <button
                      key={m}
                      onClick={() => setMode(m)}
                      className={`flex-1 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                        mode === m
                          ? "bg-blue-600 text-white"
                          : "bg-neutral-100 text-neutral-600 hover:bg-neutral-200"
                      }`}
                    >
                      {m === "file" ? "📄 File" : "✏️ Paste text"}
                    </button>
                  ))}
                </div>

                <form onSubmit={handleUpload} className="space-y-4">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-medium text-neutral-600 mb-1">
                        Source <span className="text-red-500">*</span>
                      </label>
                      <input
                        required
                        value={source}
                        onChange={(e) => setSource(e.target.value)}
                        placeholder="e.g. owasp-top10"
                        className="w-full border border-neutral-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-neutral-600 mb-1">
                        Category <span className="text-red-500">*</span>
                      </label>
                      <input
                        required
                        value={category}
                        onChange={(e) => setCategory(e.target.value)}
                        placeholder="e.g. injection"
                        className="w-full border border-neutral-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-medium text-neutral-600 mb-1">
                        Version
                      </label>
                      <input
                        value={docVersion}
                        onChange={(e) => setDocVersion(e.target.value)}
                        placeholder="1"
                        className="w-full border border-neutral-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-neutral-600 mb-1">
                        Namespace
                      </label>
                      <input
                        value={namespace}
                        onChange={(e) => setNamespace(e.target.value)}
                        placeholder="security"
                        className="w-full border border-neutral-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>

                  {mode === "file" ? (
                    <div>
                      <label className="block text-xs font-medium text-neutral-600 mb-1">
                        File (.md or .txt) <span className="text-red-500">*</span>
                      </label>
                      <input
                        ref={fileRef}
                        type="file"
                        accept=".md,.txt"
                        required
                        onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                        className="w-full text-sm text-neutral-600 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                      />
                    </div>
                  ) : (
                    <div>
                      <label className="block text-xs font-medium text-neutral-600 mb-1">
                        Content <span className="text-red-500">*</span>
                      </label>
                      <textarea
                        required
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                        rows={6}
                        placeholder="Paste your security document here..."
                        className="w-full border border-neutral-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                      />
                    </div>
                  )}

                  {uploadSuccess && (
                    <div className="rounded-lg bg-green-50 border border-green-200 px-4 py-3 text-sm text-green-700">
                      ✓ {uploadSuccess}
                    </div>
                  )}
                  {uploadError && (
                    <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
                      {uploadError}
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={uploading}
                    className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium py-2 rounded-lg text-sm transition-colors"
                  >
                    {uploading ? "Uploading…" : "Upload to Pinecone"}
                  </button>
                </form>
              </div>
            </div>

            {/* Documents list */}
            <div>
              <h2 className="text-base font-semibold text-neutral-800 mb-4">Trained documents</h2>
              {loadingDocs && (
                <div className="flex items-center justify-center py-10">
                  <div className="w-6 h-6 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
                </div>
              )}
              {docsError && (
                <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-sm text-red-700">
                  {docsError}
                </div>
              )}
              {!loadingDocs && docs.length === 0 && (
                <div className="text-center py-10 text-neutral-400 text-sm">
                  No documents ingested yet.
                </div>
              )}
              {!loadingDocs && docs.length > 0 && (
                <div className="bg-white rounded-xl border border-neutral-200 divide-y divide-neutral-100 overflow-hidden">
                  {docs.map((doc) => (
                    <div key={doc.id} className="px-5 py-4">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-neutral-900 truncate">
                            {doc.source}
                          </p>
                          <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                            <span className="text-xs bg-neutral-100 text-neutral-600 px-1.5 py-0.5 rounded">
                              {doc.category}
                            </span>
                            <span className="text-xs text-neutral-400">v{doc.doc_version}</span>
                            <span className="text-xs text-neutral-400">{doc.namespace}</span>
                          </div>
                          {doc.path && (
                            <p className="text-xs text-neutral-400 font-mono truncate mt-0.5">
                              {doc.path}
                            </p>
                          )}
                        </div>
                        <div className="text-right shrink-0">
                          <p className="text-sm font-semibold text-blue-600">{doc.chunk_count}</p>
                          <p className="text-xs text-neutral-400">chunks</p>
                        </div>
                      </div>
                      <p className="text-xs text-neutral-400 mt-2">{formatDate(doc.created_at)}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
