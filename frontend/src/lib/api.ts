const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface DumpResponse {
  success: boolean;
  entry: Record<string, unknown>;
  storage: Record<string, unknown> | null;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface EntryItem {
  id?: string;
  category: string;
  summary?: string;
  title?: string;
  content?: string;
  description?: string;
  raw_input?: string;
  tags?: string[];
  priority?: string;
  urgency?: string;
  mood?: string;
  product?: string;
  created_at?: string;
  [key: string]: unknown;
}

export async function dump(text: string): Promise<DumpResponse> {
  const res = await fetch(`${API_BASE}/dump`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to process input");
  }
  return res.json();
}

export async function chat(messages: ChatMessage[]): Promise<string> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Chat failed");
  }
  const data = await res.json();
  return data.response;
}

export async function getEntries(
  category?: string,
  limit: number = 50
): Promise<EntryItem[]> {
  const params = new URLSearchParams();
  if (category) params.set("category", category);
  params.set("limit", limit.toString());

  const res = await fetch(`${API_BASE}/entries?${params}`);
  if (!res.ok) throw new Error("Failed to fetch entries");
  const data = await res.json();
  return data.entries;
}

export async function search(
  query: string,
  categories?: string[]
): Promise<EntryItem[]> {
  const res = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, categories }),
  });
  if (!res.ok) throw new Error("Search failed");
  const data = await res.json();
  return data.results;
}

// ── Team API (Multiplayer Poke) ───────────────────────────────────────────────

function authHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const key = localStorage.getItem("cortex_api_key");
  if (!key) return {};
  return { Authorization: `Bearer ${key}` };
}

export interface Team {
  id: string;
  name: string;
  invite_code: string;
  role?: string;
}

export interface TeamMember {
  id: string;
  name: string;
  email?: string;
  role: string;
  poke_connected: boolean;
}

export async function registerUser(name: string, email?: string): Promise<{ api_key: string; user_id: string }> {
  const res = await fetch(`${API_BASE}/teams/users`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email: email || "" }),
  });
  if (!res.ok) throw new Error("Registration failed");
  const data = await res.json();
  return { api_key: data.api_key, user_id: data.user_id };
}

export async function createTeam(name: string): Promise<Team> {
  const res = await fetch(`${API_BASE}/teams`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ name }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to create team");
  }
  return res.json();
}

export async function joinTeam(inviteCode: string): Promise<Team> {
  const res = await fetch(`${API_BASE}/teams/join-with-auth`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ invite_code: inviteCode }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to join team");
  }
  const data = await res.json();
  return { id: data.team_id, name: data.team_name, invite_code: data.invite_code };
}

export async function getMyTeams(): Promise<Team[]> {
  const res = await fetch(`${API_BASE}/teams/me`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to fetch teams");
  const data = await res.json();
  return data.teams || [];
}

export async function getTeamMembers(teamId: string): Promise<TeamMember[]> {
  const res = await fetch(`${API_BASE}/teams/${teamId}/members`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to fetch members");
  const data = await res.json();
  return data.members || [];
}

export async function updatePokeKey(teamId: string, pokeApiKey: string): Promise<void> {
  const res = await fetch(`${API_BASE}/teams/${teamId}/members/me/poke-key`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ poke_api_key: pokeApiKey }),
  });
  if (!res.ok) throw new Error("Failed to update Poke key");
}

export async function findAvailability(
  teamId: string,
  startDate: string,
  endDate: string,
  durationMinutes: number = 30
): Promise<{ slots: Array<{ start: string; end: string; display: string }>; message: string }> {
  const res = await fetch(`${API_BASE}/teams/${teamId}/availability/find`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({
      start_date: startDate,
      end_date: endDate,
      duration_minutes: durationMinutes,
    }),
  });
  if (!res.ok) throw new Error("Failed to find availability");
  return res.json();
}

export async function bookMeeting(
  teamId: string,
  title: string,
  startTime: string,
  durationMinutes: number = 30
): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE}/teams/${teamId}/book`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({
      title,
      start_time: startTime,
      duration_minutes: durationMinutes,
    }),
  });
  if (!res.ok) throw new Error("Failed to book meeting");
  return res.json();
}
