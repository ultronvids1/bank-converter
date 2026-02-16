import React, { useEffect, useMemo, useState } from "react";
import { clearToken, downloadCsvUrl, downloadJsonUrl, getConversion, listConversions, login, register, setToken, uploadPdf } from "../lib/api";

type Conversion = {
  id: number;
  filename: string;
  pages: number;
  status: string;
  created_at: string;
  completed_at?: string | null;
  error_message?: string | null;
};

function Card({ children }: { children: React.ReactNode }) {
  return <div className="rounded-2xl border border-white/10 bg-white/5 p-5 shadow-sm">{children}</div>;
}

export default function App() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState<"login"|"register">("login");
  const [authed, setAuthed] = useState<boolean>(() => !!localStorage.getItem("token"));

  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [conversions, setConversions] = useState<Conversion[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    try {
      const data = await listConversions();
      setConversions(data as Conversion[]);
    } catch (e: any) {
      // ignore if not authed yet
    }
  }

  useEffect(() => { if (authed) refresh(); }, [authed]);

  async function onAuth() {
    setError(null);
    try {
      if (mode === "register") await register(email, password);
      const tok = await login(email, password) as any;
      setToken(tok.access_token);
      setAuthed(true);
      refresh();
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function onUpload() {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const res = await uploadPdf(file) as any;
      const id = res.conversion_id as number;

      // Poll for completion
      for (let i=0; i<60; i++) {
        await new Promise(r => setTimeout(r, 1000));
        const c = await getConversion(id) as any;
        if (c.status === "done" || c.status === "failed") break;
      }
      await refresh();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setUploading(false);
    }
  }

  function logout() {
    clearToken();
    setAuthed(false);
    setConversions([]);
  }

  return (
    <div className="min-h-screen">
      <div className="mx-auto max-w-5xl p-6">
        <header className="mb-8 flex items-center justify-between">
          <div>
            <div className="text-sm text-white/60">Bank Statement Converter</div>
            <h1 className="text-2xl font-semibold tracking-tight">PDF → CSV / JSON</h1>
          </div>
          {authed ? (
            <button onClick={logout} className="rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm hover:bg-white/10">
              Log out
            </button>
          ) : null}
        </header>

        {!authed ? (
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <h2 className="text-lg font-medium mb-2">{mode === "login" ? "Log in" : "Create account"}</h2>
              <p className="text-sm text-white/60 mb-4">Use any email for local/dev. Hook up Stripe later.</p>
              <div className="space-y-3">
                <input className="w-full rounded-xl bg-black/40 border border-white/10 px-3 py-2"
                  placeholder="Email" value={email} onChange={e=>setEmail(e.target.value)} />
                <input className="w-full rounded-xl bg-black/40 border border-white/10 px-3 py-2"
                  placeholder="Password" type="password" value={password} onChange={e=>setPassword(e.target.value)} />
                <button onClick={onAuth} className="w-full rounded-xl bg-white text-black px-4 py-2 font-medium hover:opacity-90">
                  {mode === "login" ? "Log in" : "Register"}
                </button>
                <button onClick={()=>setMode(mode==="login"?"register":"login")} className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm hover:bg-white/10">
                  {mode === "login" ? "Need an account? Register" : "Already have an account? Log in"}
                </button>
                {error ? <div className="text-sm text-red-300 whitespace-pre-wrap">{error}</div> : null}
              </div>
            </Card>
            <Card>
              <h2 className="text-lg font-medium mb-2">What this MVP does</h2>
              <ul className="text-sm text-white/70 space-y-2 list-disc pl-5">
                <li>Uploads a PDF, processes it in a background worker.</li>
                <li>Extracts tables (pdfplumber → Camelot → PyMuPDF), then OCR fallback.</li>
                <li>Outputs CSV + JSON.</li>
                <li>Shows conversion history + download links.</li>
              </ul>
              <div className="mt-4 text-xs text-white/50">
                Tip: For best accuracy, test with statements that have clear transaction tables.
              </div>
            </Card>
          </div>
        ) : (
          <div className="grid gap-6">
            <Card>
              <h2 className="text-lg font-medium mb-2">Upload PDF</h2>
              <div className="flex flex-col gap-3 md:flex-row md:items-center">
                <input
                  type="file"
                  accept="application/pdf"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="block w-full text-sm text-white/70 file:mr-4 file:rounded-xl file:border-0 file:bg-white file:px-4 file:py-2 file:font-medium file:text-black hover:file:opacity-90"
                />
                <button
                  onClick={onUpload}
                  disabled={!file || uploading}
                  className="rounded-xl bg-white text-black px-5 py-2 font-medium disabled:opacity-50"
                >
                  {uploading ? "Processing..." : "Convert"}
                </button>
              </div>
              {error ? <div className="mt-3 text-sm text-red-300 whitespace-pre-wrap">{error}</div> : null}
            </Card>

            <Card>
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-medium">History</h2>
                <button onClick={refresh} className="rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm hover:bg-white/10">
                  Refresh
                </button>
              </div>

              <div className="mt-4 overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="text-white/60">
                    <tr>
                      <th className="py-2 text-left">File</th>
                      <th className="py-2 text-left">Status</th>
                      <th className="py-2 text-left">Pages</th>
                      <th className="py-2 text-left">Created</th>
                      <th className="py-2 text-left">Downloads</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/10">
                    {conversions.map(c => (
                      <tr key={c.id}>
                        <td className="py-3">{c.filename}</td>
                        <td className="py-3">
                          <span className={
                            "rounded-full px-2 py-1 text-xs " +
                            (c.status==="done" ? "bg-green-500/15 text-green-200" :
                             c.status==="failed" ? "bg-red-500/15 text-red-200" :
                             "bg-white/10 text-white/70")
                          }>
                            {c.status}
                          </span>
                          {c.error_message ? <div className="text-xs text-red-200/80 mt-1">{c.error_message}</div> : null}
                        </td>
                        <td className="py-3">{c.pages ?? "-"}</td>
                        <td className="py-3 text-white/70">{new Date(c.created_at).toLocaleString()}</td>
                        <td className="py-3">
                          {c.status === "done" ? (
                            <div className="flex gap-2">
                              <a className="rounded-lg border border-white/10 bg-white/5 px-3 py-1 hover:bg-white/10"
                                 href={downloadCsvUrl(c.id)} target="_blank" rel="noreferrer">CSV</a>
                              <a className="rounded-lg border border-white/10 bg-white/5 px-3 py-1 hover:bg-white/10"
                                 href={downloadJsonUrl(c.id)} target="_blank" rel="noreferrer">JSON</a>
                            </div>
                          ) : (
                            <span className="text-white/50">—</span>
                          )}
                        </td>
                      </tr>
                    ))}
                    {conversions.length === 0 ? (
                      <tr><td className="py-6 text-white/50" colSpan={5}>No conversions yet.</td></tr>
                    ) : null}
                  </tbody>
                </table>
              </div>
            </Card>
          </div>
        )}

        <footer className="mt-10 text-xs text-white/40">
          MVP build: FastAPI + Celery + Redis + Postgres + React.
        </footer>
      </div>
    </div>
  );
}
