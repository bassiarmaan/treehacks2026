"use client";

import { useState, useEffect, useCallback } from "react";
import {
  CheckSquare,
  Lightbulb,
  ShoppingCart,
  FileText,
  Users,
  Heart,
  UserPlus,
  Calendar,
  RefreshCw,
} from "lucide-react";
import { getEntries, type EntryItem } from "@/lib/api";
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

const ALL_CATEGORIES = [
  "task",
  "idea",
  "shopping",
  "note",
  "meeting",
  "reflection",
  "contact",
  "event",
];

export default function EntriesFeed({ refreshTrigger }: { refreshTrigger: number }) {
  const [entries, setEntries] = useState<EntryItem[]>([]);
  const [filter, setFilter] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchEntries = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getEntries(filter || undefined);
      setEntries(data);
    } catch {
      // Silently fail - entries just won't show
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    fetchEntries();
  }, [fetchEntries, refreshTrigger]);

  return (
    <div className="space-y-4">
      {/* Filter pills */}
      <div className="flex items-center gap-2 flex-wrap">
        <button
          onClick={() => setFilter(null)}
          className={`rounded-full px-3 py-1 text-xs font-medium border transition-all ${
            filter === null
              ? "bg-violet-600/20 border-violet-500/40 text-violet-300"
              : "bg-zinc-800/50 border-zinc-700 text-zinc-400 hover:border-zinc-600"
          }`}
        >
          All
        </button>
        {ALL_CATEGORIES.map((cat) => {
          const config = CATEGORY_CONFIG[cat];
          return (
            <button
              key={cat}
              onClick={() => setFilter(filter === cat ? null : cat)}
              className={`rounded-full px-3 py-1 text-xs font-medium border transition-all ${
                filter === cat
                  ? `${config.bgColor} ${config.color}`
                  : "bg-zinc-800/50 border-zinc-700 text-zinc-400 hover:border-zinc-600"
              }`}
            >
              {config.label}
            </button>
          );
        })}
        <button
          onClick={fetchEntries}
          className="ml-auto text-zinc-500 hover:text-zinc-300 transition-colors"
          title="Refresh"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Entries list */}
      {entries.length === 0 ? (
        <div className="text-center py-12 text-zinc-500 text-sm">
          {loading ? "Loading..." : "No entries yet. Start dumping thoughts above!"}
        </div>
      ) : (
        <div className="space-y-2">
          {entries.map((entry, i) => {
            const category = entry.category || "note";
            const config = CATEGORY_CONFIG[category] || CATEGORY_CONFIG.note;
            const Icon = ICON_MAP[config.icon] || FileText;

            return (
              <div
                key={entry.id || i}
                className={`rounded-xl border ${config.bgColor} px-4 py-3 space-y-2 transition-all hover:scale-[1.01]`}
              >
                <div className="flex items-center gap-2">
                  <Icon className={`w-4 h-4 ${config.color}`} />
                  <span className={`text-xs font-semibold uppercase tracking-wider ${config.color}`}>
                    {config.label}
                  </span>
                  {entry.created_at && (
                    <span className="text-xs text-zinc-500 ml-auto">
                      {new Date(entry.created_at).toLocaleDateString()}
                    </span>
                  )}
                </div>

                <p className="text-sm text-zinc-300">
                  {(entry.summary as string) ||
                    (entry.title as string) ||
                    (entry.raw_input as string)?.slice(0, 150)}
                </p>

                {entry.tags && entry.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {entry.tags.map((tag, j) => (
                      <span
                        key={j}
                        className="rounded-full bg-zinc-800/80 px-2 py-0.5 text-[10px] text-zinc-400 border border-zinc-700/50"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
