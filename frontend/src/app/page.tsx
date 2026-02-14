"use client";

import { useState } from "react";
import { Brain, Inbox, MessageSquare, LayoutDashboard, Users } from "lucide-react";
import DumpBox from "@/components/DumpBox";
import ChatInterface from "@/components/ChatInterface";
import EntriesFeed from "@/components/EntriesFeed";
import TeamDashboard from "@/components/TeamDashboard";

type Tab = "dump" | "chat" | "entries" | "team";

export default function Home() {
  const [activeTab, setActiveTab] = useState<Tab>("dump");
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleNewEntry = () => {
    setRefreshTrigger((prev) => prev + 1);
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-zinc-800/50 bg-zinc-950/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-3xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-600 to-purple-600 flex items-center justify-center">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <div>
            <h1 className="text-lg font-bold tracking-tight">Team Brain</h1>
            <p className="text-xs text-zinc-500">Multiplayer Poke - Shared team coordination</p>
            </div>
          </div>
        </div>
      </header>

      {/* Tabs */}
      <div className="border-b border-zinc-800/50 bg-zinc-950/50">
        <div className="max-w-3xl mx-auto px-4">
          <nav className="flex gap-1">
            {[
              { id: "team" as Tab, label: "Team", icon: Users },
              { id: "dump" as Tab, label: "Dump", icon: Inbox },
              { id: "chat" as Tab, label: "Chat", icon: MessageSquare },
              { id: "entries" as Tab, label: "Entries", icon: LayoutDashboard },
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-all ${
                  activeTab === id
                    ? "border-violet-500 text-violet-400"
                    : "border-transparent text-zinc-500 hover:text-zinc-300"
                }`}
              >
                <Icon className="w-4 h-4" />
                {label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Content */}
      <main className="flex-1 max-w-3xl mx-auto w-full px-4 py-8">
        {activeTab === "team" && <TeamDashboard />}

        {activeTab === "dump" && (
          <div className="space-y-8">
            <div className="text-center space-y-2">
              <h2 className="text-2xl font-bold">What&apos;s on your mind?</h2>
              <p className="text-zinc-500 text-sm">
                Dump anything -- tasks, ideas, shopping lists, meeting notes,
                random thoughts. AI handles the rest.
              </p>
            </div>
            <DumpBox onNewEntry={handleNewEntry} />
          </div>
        )}

        {activeTab === "chat" && (
          <div className="h-[calc(100vh-220px)]">
            <ChatInterface />
          </div>
        )}

        {activeTab === "entries" && <EntriesFeed refreshTrigger={refreshTrigger} />}
      </main>

      {/* Footer */}
      <footer className="border-t border-zinc-800/50 py-4">
        <div className="max-w-3xl mx-auto px-4 flex items-center justify-between text-xs text-zinc-600">
          <span>Built at TreeHacks 2026</span>
          <span>Poke + Claude + Elasticsearch + Stagehand</span>
        </div>
      </footer>
    </div>
  );
}
