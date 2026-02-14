"use client";

import { useState } from "react";
import { Users, Key, Copy, Check } from "lucide-react";
import {
  registerUser,
  createTeam,
  joinTeam,
  getMyTeams,
  type Team,
} from "@/lib/api";

type Step = "register" | "create-or-join" | "create" | "join" | "done";

export default function TeamSetup({
  onComplete,
  initialApiKey,
}: {
  onComplete: (team: Team) => void;
  initialApiKey?: string | null;
}) {
  const [step, setStep] = useState<Step>(initialApiKey ? "create-or-join" : "register");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [teamName, setTeamName] = useState("");
  const [inviteCode, setInviteCode] = useState("");
  const [apiKey, setApiKey] = useState(initialApiKey || "");
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  const handleRegister = async () => {
    if (!name.trim()) return;
    setError("");
    try {
      const { api_key } = await registerUser(name.trim(), email.trim());
      setApiKey(api_key);
      localStorage.setItem("cortex_api_key", api_key);
      setStep("create-or-join");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Registration failed");
    }
  };

  const handleCreateTeam = async () => {
    if (!teamName.trim()) return;
    setError("");
    try {
      const team = await createTeam(teamName.trim());
      setStep("done");
      onComplete(team);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create team");
    }
  };

  const handleJoinTeam = async () => {
    if (!inviteCode.trim()) return;
    setError("");
    try {
      const team = await joinTeam(inviteCode.trim().toUpperCase());
      setStep("done");
      onComplete(team);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to join team");
    }
  };

  const copyKey = () => {
    navigator.clipboard.writeText(apiKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (step === "register") {
    return (
      <div className="space-y-6 max-w-md mx-auto">
        <div className="text-center space-y-2">
          <Users className="w-12 h-12 mx-auto text-violet-500" />
          <h2 className="text-xl font-bold">Get Started</h2>
          <p className="text-sm text-zinc-500">
            Enter your name to create an account and connect to Team Brain.
          </p>
        </div>
        <div className="space-y-4">
          <input
            type="text"
            placeholder="Your name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-xl bg-zinc-800/50 border border-zinc-700 px-4 py-3 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-violet-500/50"
          />
          <input
            type="email"
            placeholder="Email (optional)"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-xl bg-zinc-800/50 border border-zinc-700 px-4 py-3 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-violet-500/50"
          />
          {error && <p className="text-sm text-red-400">{error}</p>}
          <button
            onClick={handleRegister}
            disabled={!name.trim()}
            className="w-full rounded-xl bg-violet-600 py-3 font-medium text-white hover:bg-violet-500 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Continue
          </button>
        </div>
      </div>
    );
  }

  if (step === "create-or-join") {
    return (
      <div className="space-y-6 max-w-md mx-auto">
        <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-amber-400">Your API Key</span>
            <button
              onClick={copyKey}
              className="flex items-center gap-1 text-xs text-zinc-400 hover:text-zinc-200"
            >
              {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
              {copied ? "Copied" : "Copy"}
            </button>
          </div>
          <code className="text-xs text-zinc-400 break-all block">{apiKey}</code>
          <p className="text-xs text-zinc-500">
            Add this to Poke at poke.com/settings/connections when connecting Team Brain.
          </p>
        </div>
        <div className="text-center space-y-2">
          <h2 className="text-xl font-bold">Create or Join a Team</h2>
          <p className="text-sm text-zinc-500">
            Create a new team or join one with an invite code.
          </p>
        </div>
        <div className="flex gap-4">
          <button
            onClick={() => setStep("create")}
            className="flex-1 rounded-xl border border-zinc-700 py-3 font-medium text-zinc-300 hover:border-violet-500/50 hover:text-violet-400"
          >
            Create Team
          </button>
          <button
            onClick={() => setStep("join")}
            className="flex-1 rounded-xl border border-zinc-700 py-3 font-medium text-zinc-300 hover:border-violet-500/50 hover:text-violet-400"
          >
            Join Team
          </button>
        </div>
      </div>
    );
  }

  if (step === "create") {
    return (
      <div className="space-y-6 max-w-md mx-auto">
        <div className="text-center space-y-2">
          <h2 className="text-xl font-bold">Create a Team</h2>
          <p className="text-sm text-zinc-500">Give your team a name.</p>
        </div>
        <div className="space-y-4">
          <input
            type="text"
            placeholder="Team name (e.g. Bruin Sports Analytics)"
            value={teamName}
            onChange={(e) => setTeamName(e.target.value)}
            className="w-full rounded-xl bg-zinc-800/50 border border-zinc-700 px-4 py-3 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-violet-500/50"
          />
          {error && <p className="text-sm text-red-400">{error}</p>}
          <div className="flex gap-2">
            <button
              onClick={() => setStep("create-or-join")}
              className="rounded-xl border border-zinc-700 px-4 py-2 text-sm text-zinc-400 hover:text-zinc-200"
            >
              Back
            </button>
            <button
              onClick={handleCreateTeam}
              disabled={!teamName.trim()}
              className="flex-1 rounded-xl bg-violet-600 py-2 font-medium text-white hover:bg-violet-500 disabled:opacity-40"
            >
              Create
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (step === "join") {
    return (
      <div className="space-y-6 max-w-md mx-auto">
        <div className="text-center space-y-2">
          <h2 className="text-xl font-bold">Join a Team</h2>
          <p className="text-sm text-zinc-500">Enter the invite code from your teammate.</p>
        </div>
        <div className="space-y-4">
          <input
            type="text"
            placeholder="Invite code (e.g. A1B2C3D4)"
            value={inviteCode}
            onChange={(e) => setInviteCode(e.target.value.toUpperCase())}
            className="w-full rounded-xl bg-zinc-800/50 border border-zinc-700 px-4 py-3 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-violet-500/50 uppercase"
          />
          {error && <p className="text-sm text-red-400">{error}</p>}
          <div className="flex gap-2">
            <button
              onClick={() => setStep("create-or-join")}
              className="rounded-xl border border-zinc-700 px-4 py-2 text-sm text-zinc-400 hover:text-zinc-200"
            >
              Back
            </button>
            <button
              onClick={handleJoinTeam}
              disabled={!inviteCode.trim()}
              className="flex-1 rounded-xl bg-violet-600 py-2 font-medium text-white hover:bg-violet-500 disabled:opacity-40"
            >
              Join
            </button>
          </div>
        </div>
      </div>
    );
  }

  return null;
}
