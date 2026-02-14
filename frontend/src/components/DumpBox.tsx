"use client";

import { useState, useRef, useEffect } from "react";
import {
  Send,
  Loader2,
  Sparkles,
  CheckSquare,
  Lightbulb,
  ShoppingCart,
  FileText,
  Users,
  Heart,
  UserPlus,
  Calendar,
  Brain,
} from "lucide-react";
import { dump, type DumpResponse } from "@/lib/api";
import { CATEGORY_CONFIG } from "@/lib/categories";

const ICON_MAP: Record<string, React.ElementType> = {
  CheckSquare,
  Lightbulb,
  ShoppingCart,
  FileText,
  Users,
  Heart,
  UserPlus,
  Calendar,
};

interface ClassifiedEntry {
  entry: Record<string, unknown>;
  timestamp: Date;
}

export default function DumpBox({
  onNewEntry,
}: {
  onNewEntry?: (entry: Record<string, unknown>) => void;
}) {
  const [input, setInput] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [lastResult, setLastResult] = useState<ClassifiedEntry | null>(null);
  const [error, setError] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [placeholderIdx, setPlaceholderIdx] = useState(0);

  const placeholders = [
    "Buy milk, eggs, and bread this weekend...",
    "Idea: an app that organizes your fridge with AI...",
    "Meeting with Sarah at 2pm about Q4 numbers...",
    "Need to finish the pitch deck by Friday...",
    "Feeling grateful for the team today...",
    "John Smith, met at TreeHacks, works at Stripe...",
  ];

  useEffect(() => {
    textareaRef.current?.focus();
    const interval = setInterval(() => {
      setPlaceholderIdx((i) => (i + 1) % placeholders.length);
    }, 4000);
    return () => clearInterval(interval);
  }, [placeholders.length]);

  const handleSubmit = async () => {
    const text = input.trim();
    if (!text || isProcessing) return;

    setIsProcessing(true);
    setError(null);

    try {
      const result: DumpResponse = await dump(text);
      const entry: ClassifiedEntry = {
        entry: result.entry,
        timestamp: new Date(),
      };
      setLastResult(entry);
      setInput("");
      onNewEntry?.(result.entry);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const category = lastResult?.entry?.category as string | undefined;
  const config = category ? CATEGORY_CONFIG[category] : null;
  const IconComponent = config ? ICON_MAP[config.icon] : null;

  return (
    <div className="w-full max-w-2xl mx-auto space-y-6">
      {/* Main input area */}
      <div
        className={`relative rounded-2xl border border-zinc-800 bg-zinc-900/50 backdrop-blur-sm transition-all duration-300 ${
          isProcessing ? "processing border-violet-500/40" : "hover:border-zinc-700 focus-within:border-violet-500/50"
        }`}
      >
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholders[placeholderIdx]}
          rows={3}
          className="w-full resize-none bg-transparent px-5 pt-5 pb-14 text-zinc-100 placeholder-zinc-500 focus:outline-none text-base leading-relaxed"
          disabled={isProcessing}
        />

        {/* Bottom bar */}
        <div className="absolute bottom-0 left-0 right-0 flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2 text-xs text-zinc-500">
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI auto-classifies your input</span>
          </div>
          <button
            onClick={handleSubmit}
            disabled={!input.trim() || isProcessing}
            className="flex items-center gap-2 rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white transition-all hover:bg-violet-500 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {isProcessing ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
            {isProcessing ? "Processing..." : "Dump"}
          </button>
        </div>
      </div>

      {/* Error display */}
      {error && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/5 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Classification result */}
      {lastResult && config && (
        <div
          className={`rounded-xl border ${config.bgColor} px-5 py-4 space-y-3 animate-in fade-in slide-in-from-bottom-2 duration-300`}
        >
          <div className="flex items-center gap-3">
            {IconComponent && (
              <IconComponent className={`w-5 h-5 ${config.color}`} />
            )}
            <span
              className={`text-sm font-semibold uppercase tracking-wider ${config.color}`}
            >
              {config.label}
            </span>
          </div>

          {/* Summary */}
          <p className="text-zinc-300 text-sm">
            {(lastResult.entry.summary as string) || "Processed successfully"}
          </p>

          {/* Structured fields */}
          <div className="flex flex-wrap gap-2">
            {(lastResult.entry.tags as string[])?.map(
              (tag: string, i: number) => (
                <span
                  key={i}
                  className="rounded-full bg-zinc-800 px-2.5 py-0.5 text-xs text-zinc-400 border border-zinc-700"
                >
                  {tag}
                </span>
              )
            )}
            {typeof lastResult.entry.priority === "string" && (
              <span className="rounded-full bg-zinc-800 px-2.5 py-0.5 text-xs text-zinc-400 border border-zinc-700">
                Priority: {lastResult.entry.priority}
              </span>
            )}
            {typeof lastResult.entry.urgency === "string" && (
              <span className="rounded-full bg-zinc-800 px-2.5 py-0.5 text-xs text-zinc-400 border border-zinc-700">
                Urgency: {lastResult.entry.urgency}
              </span>
            )}
            {typeof lastResult.entry.mood === "string" && (
              <span className="rounded-full bg-zinc-800 px-2.5 py-0.5 text-xs text-zinc-400 border border-zinc-700">
                Mood: {lastResult.entry.mood}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
