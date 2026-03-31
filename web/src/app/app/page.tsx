"use client";

import { useState, useRef, DragEvent, ChangeEvent } from "react";
import { useRouter } from "next/navigation";

const ACCEPTED_TYPES = ".mp3,.mp4,.m4a,.wav,.webm,.ogg,.flac";

const TRANSCRIPTION_MODELS = ["gpt-4o-transcribe", "whisper-1"];
const CLEANUP_MODELS = ["gpt-4.1-mini", "gpt-4.1", "gpt-4o-mini"];

export default function AppPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [cleanupEnabled, setCleanupEnabled] = useState(true);
  const [transcriptionModel, setTranscriptionModel] = useState(
    TRANSCRIPTION_MODELS[0]
  );
  const [cleanupModel, setCleanupModel] = useState(CLEANUP_MODELS[0]);
  const [transcription, setTranscription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const [statusMsg, setStatusMsg] = useState("");
  const statusTimers = useRef<ReturnType<typeof setTimeout>[]>([]);

  function handleDragOver(e: DragEvent) {
    e.preventDefault();
    setDragging(true);
  }

  function handleDragLeave(e: DragEvent) {
    e.preventDefault();
    setDragging(false);
  }

  function handleDrop(e: DragEvent) {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) setFile(dropped);
  }

  function handleFileChange(e: ChangeEvent<HTMLInputElement>) {
    const selected = e.target.files?.[0];
    if (selected) setFile(selected);
  }

  async function handleTranscribe() {
    if (!file) return;
    setLoading(true);
    setError("");
    setTranscription("");
    setStatusMsg("Enviando archivo...");
    statusTimers.current.forEach(clearTimeout);
    statusTimers.current = [
      setTimeout(() => setStatusMsg("Transcribiendo con OpenAI..."), 4000),
      setTimeout(() => setStatusMsg(cleanupEnabled ? "Esperando respuesta..." : "Casi listo..."), 18000),
      setTimeout(() => setStatusMsg(cleanupEnabled ? "Limpiando texto..." : "Finalizando..."), 35000),
    ];

    try {
      const formData = new FormData();
      formData.append("audio", file);
      formData.append("skipCleanup", cleanupEnabled ? "false" : "true");
      formData.append("transcriptionModel", transcriptionModel);
      formData.append("cleanupModel", cleanupModel);

      const res = await fetch("/api/transcribe", {
        method: "POST",
        body: formData,
      });

      if (res.status === 401) {
        router.push("/login");
        return;
      }

      const data = await res.json();

      if (!res.ok) {
        setError(data.error ?? "Transcription failed");
        return;
      }

      setTranscription(data.text);
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      statusTimers.current.forEach(clearTimeout);
      statusTimers.current = [];
      setStatusMsg("");
      setLoading(false);
    }
  }

  async function handleLogout() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/login");
  }

  async function handleCopy() {
    await navigator.clipboard.writeText(transcription);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  const wordCount = transcription
    ? transcription.trim().split(/\s+/).length
    : 0;
  const charCount = transcription.length;

  return (
    <div className="min-h-screen flex flex-col">
      {/* Navbar */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-dark-border">
        <div className="flex items-center gap-2">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={2}
            strokeLinecap="round"
            strokeLinejoin="round"
            className="w-6 h-6 text-dark-accent"
          >
            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
            <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
            <line x1="12" x2="12" y1="19" y2="22" />
          </svg>
          <span className="text-lg font-semibold text-dark-text">
            AudioText
          </span>
        </div>
        <button
          onClick={handleLogout}
          className="text-sm text-dark-muted hover:text-dark-text transition-colors"
        >
          Cerrar sesion
        </button>
      </header>

      {/* Main content */}
      <main className="flex-1 flex flex-col lg:flex-row">
        {/* Left panel - Upload & Options */}
        <section className="w-full lg:w-[420px] lg:min-w-[420px] border-b lg:border-b-0 lg:border-r border-dark-border p-6 flex flex-col gap-6">
          {/* Drop zone */}
          <div
            onClick={() => fileInputRef.current?.click()}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`relative flex flex-col items-center justify-center gap-3 p-8 rounded-xl border-2 border-dashed cursor-pointer transition-colors ${
              dragging
                ? "border-dark-accent bg-dark-accent/10"
                : "border-dark-border hover:border-dark-muted"
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept={ACCEPTED_TYPES}
              onChange={handleFileChange}
              className="hidden"
            />

            {/* Upload icon */}
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={1.5}
              strokeLinecap="round"
              strokeLinejoin="round"
              className="w-10 h-10 text-dark-muted"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" x2="12" y1="3" y2="15" />
            </svg>

            {file ? (
              <div className="text-center">
                <p className="text-sm font-medium text-dark-text">
                  {file.name}
                </p>
                <p className="text-xs text-dark-muted mt-1">
                  {(file.size / (1024 * 1024)).toFixed(1)} MB
                </p>
              </div>
            ) : (
              <div className="text-center">
                <p className="text-sm text-dark-muted">
                  Arrastra un archivo de audio o haz clic para buscar
                </p>
                <p className="text-xs text-dark-muted/60 mt-1">
                  MP3, MP4, M4A, WAV, WebM, OGG, FLAC
                </p>
              </div>
            )}
          </div>

          {/* Options */}
          <div className="space-y-4">
            <h2 className="text-sm font-medium text-dark-muted uppercase tracking-wider">
              Opciones
            </h2>

            {/* Cleanup toggle */}
            <div className="flex items-center justify-between">
              <label
                htmlFor="cleanup-toggle"
                className="text-sm text-dark-text"
              >
                Limpiar transcripcion
              </label>
              <button
                id="cleanup-toggle"
                role="switch"
                aria-checked={cleanupEnabled}
                onClick={() => setCleanupEnabled(!cleanupEnabled)}
                className={`relative w-11 h-6 rounded-full transition-colors ${
                  cleanupEnabled ? "bg-dark-accent" : "bg-dark-border"
                }`}
              >
                <span
                  className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform ${
                    cleanupEnabled ? "translate-x-5" : "translate-x-0"
                  }`}
                />
              </button>
            </div>

            {/* Transcription model */}
            <div>
              <label
                htmlFor="transcription-model"
                className="block text-sm text-dark-text mb-1.5"
              >
                Modelo de transcripcion
              </label>
              <select
                id="transcription-model"
                value={transcriptionModel}
                onChange={(e) => setTranscriptionModel(e.target.value)}
                className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-dark-text text-sm focus:outline-none focus:ring-2 focus:ring-dark-accent/50 focus:border-dark-accent transition-colors"
              >
                {TRANSCRIPTION_MODELS.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </div>

            {/* Cleanup model */}
            {cleanupEnabled && (
              <div>
                <label
                  htmlFor="cleanup-model"
                  className="block text-sm text-dark-text mb-1.5"
                >
                  Modelo de limpieza
                </label>
                <select
                  id="cleanup-model"
                  value={cleanupModel}
                  onChange={(e) => setCleanupModel(e.target.value)}
                  className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-dark-text text-sm focus:outline-none focus:ring-2 focus:ring-dark-accent/50 focus:border-dark-accent transition-colors"
                >
                  {CLEANUP_MODELS.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {/* Transcribe button */}
          <button
            onClick={handleTranscribe}
            disabled={!file || loading}
            className="w-full py-3 bg-dark-accent hover:bg-dark-accent/90 text-white font-medium rounded-lg focus:outline-none focus:ring-2 focus:ring-dark-accent/50 focus:ring-offset-2 focus:ring-offset-dark-bg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Transcribir
          </button>

          {statusMsg && (
            <div className="flex items-center gap-2 text-sm text-dark-muted">
              <div className="w-3.5 h-3.5 border-2 border-dark-accent border-t-transparent rounded-full animate-spin flex-shrink-0" />
              <span>{statusMsg}</span>
            </div>
          )}

          {error && (
            <p className="text-sm text-red-400 bg-red-400/10 border border-red-400/20 rounded-lg px-3 py-2">
              {error}
            </p>
          )}
        </section>

        {/* Right panel - Result */}
        <section className="flex-1 p-6 flex flex-col min-h-[420px] lg:min-h-0">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-medium text-dark-muted uppercase tracking-wider">
              Transcripcion
            </h2>
            {transcription && (
              <div className="flex items-center gap-3">
                <span className="text-xs text-dark-muted">
                  {wordCount} palabras &middot; {charCount} caracteres
                </span>
                <button
                  onClick={handleCopy}
                  title={copied ? "Copiado" : "Copiar al portapapeles"}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium transition-all ${
                    copied
                      ? "bg-green-500/10 border-green-500/30 text-green-400"
                      : "bg-dark-surface border-dark-border text-dark-accent hover:bg-dark-border hover:text-white"
                  }`}
                >
                  {copied ? (
                    <>
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round" className="w-3.5 h-3.5">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                      Copiado
                    </>
                  ) : (
                    <>
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className="w-3.5 h-3.5">
                        <rect width="14" height="14" x="8" y="8" rx="2" ry="2" />
                        <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2" />
                      </svg>
                      Copiar
                    </>
                  )}
                </button>
              </div>
            )}
          </div>

          <div className="flex-1 bg-dark-surface border border-dark-border rounded-xl p-6 overflow-y-auto">
            {loading ? (
              <div className="space-y-3 animate-pulse">
                <div className="h-4 bg-dark-border rounded w-3/4" />
                <div className="h-4 bg-dark-border rounded w-full" />
                <div className="h-4 bg-dark-border rounded w-5/6" />
                <div className="h-4 bg-dark-border rounded w-2/3" />
                <div className="h-4 bg-dark-border rounded w-full" />
                <div className="h-4 bg-dark-border rounded w-4/5" />
              </div>
            ) : transcription ? (
              <p className="text-dark-text leading-relaxed whitespace-pre-wrap">
                {transcription}
              </p>
            ) : (
              <p className="text-dark-muted/50 text-center mt-20">
                Tu transcripcion aparecera aqui...
              </p>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
