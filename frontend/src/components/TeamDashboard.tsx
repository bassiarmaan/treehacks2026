"use client";

import { useState, useEffect } from "react";
import { Users, Copy, Check, Key, RefreshCw } from "lucide-react";
import {
  getMyTeams,
  getTeamMembers,
  updatePokeKey,
  type Team,
  type TeamMember,
} from "@/lib/api";
import TeamSetup from "./TeamSetup";
import CalendarView from "./CalendarView";

export default function TeamDashboard() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [selectedTeam, setSelectedTeam] = useState<Team | null>(null);
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [pokeKeyInput, setPokeKeyInput] = useState("");
  const [copied, setCopied] = useState(false);

  const fetchTeams = async () => {
    const key = localStorage.getItem("cortex_api_key");
    if (!key) {
      setLoading(false);
      return;
    }
    try {
      const t = await getMyTeams();
      setTeams(t);
      if (t.length > 0 && !selectedTeam) setSelectedTeam(t[0]);
    } catch {
      setTeams([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchMembers = async () => {
    if (!selectedTeam) return;
    try {
      const m = await getTeamMembers(selectedTeam.id);
      setMembers(m);
    } catch {
      setMembers([]);
    }
  };

  useEffect(() => {
    fetchTeams();
  }, []);

  useEffect(() => {
    if (selectedTeam) fetchMembers();
  }, [selectedTeam]);

  const handleSetupComplete = (team: Team) => {
    setTeams([team]);
    setSelectedTeam(team);
    setLoading(false);
  };

  const copyInviteLink = () => {
    if (!selectedTeam) return;
    const url = `${typeof window !== "undefined" ? window.location.origin : ""}/team?join=${selectedTeam.invite_code}`;
    navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const copyInviteCode = () => {
    if (!selectedTeam) return;
    navigator.clipboard.writeText(selectedTeam.invite_code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSavePokeKey = async () => {
    if (!selectedTeam || !pokeKeyInput.trim()) return;
    try {
      await updatePokeKey(selectedTeam.id, pokeKeyInput.trim());
      setPokeKeyInput("");
      fetchMembers();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Failed to save");
    }
  };

  const apiKey = typeof window !== "undefined" ? localStorage.getItem("cortex_api_key") : null;

  if (!apiKey) {
    return (
      <div className="space-y-8">
        <TeamSetup onComplete={handleSetupComplete} />
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-pulse text-zinc-500">Loading...</div>
      </div>
    );
  }

  if (teams.length === 0) {
    return (
      <div className="space-y-8">
        <TeamSetup onComplete={handleSetupComplete} initialApiKey={apiKey} />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="space-y-4">
        <h2 className="text-xl font-bold">Team: {selectedTeam?.name}</h2>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={copyInviteCode}
            className="flex items-center gap-2 rounded-xl border border-zinc-700 bg-zinc-800/50 px-4 py-2 text-sm text-zinc-300 hover:border-violet-500/50"
          >
            Invite code: {selectedTeam?.invite_code}
            {copied ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
          </button>
        </div>
      </div>

      <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 space-y-4">
        <h3 className="font-semibold flex items-center gap-2">
          <Key className="w-4 h-4" />
          Connect Poke for Calendar Sync
        </h3>
        <p className="text-sm text-zinc-500">
          Add your Poke API key so the team can find times when you&apos;re free.
          Get it at poke.com/settings/advanced
        </p>
        <div className="flex gap-2">
          <input
            type="password"
            placeholder="Poke API key"
            value={pokeKeyInput}
            onChange={(e) => setPokeKeyInput(e.target.value)}
            className="flex-1 rounded-xl bg-zinc-800 border border-zinc-700 px-4 py-2 text-sm text-zinc-100 placeholder-zinc-500"
          />
          <button
            onClick={handleSavePokeKey}
            disabled={!pokeKeyInput.trim()}
            className="rounded-xl bg-violet-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
          >
            Save
          </button>
        </div>
      </div>

      <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 space-y-4">
        <h3 className="font-semibold flex items-center gap-2">
          <Users className="w-4 h-4" />
          Members
          <button onClick={fetchMembers} className="text-zinc-500 hover:text-zinc-300">
            <RefreshCw className="w-4 h-4" />
          </button>
        </h3>
        {members.length === 0 ? (
          <p className="text-sm text-zinc-500">No members yet. Share the invite code!</p>
        ) : (
          <ul className="space-y-2">
            {members.map((m) => (
              <li
                key={m.id}
                className="flex items-center justify-between rounded-lg bg-zinc-800/50 px-3 py-2"
              >
                <span>{m.name}</span>
                <span
                  className={`text-xs ${m.poke_connected ? "text-green-500" : "text-zinc-500"}`}
                >
                  {m.poke_connected ? "Poke connected" : "No Poke"}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {selectedTeam && <CalendarView team={selectedTeam} />}
    </div>
  );
}
