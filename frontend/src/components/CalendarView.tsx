"use client";

import { useState, useEffect } from "react";
import { Calendar, Loader2, Clock } from "lucide-react";
import { findAvailability, bookMeeting, type Team } from "@/lib/api";

function getWeekRange(): { start: string; end: string } {
  const now = new Date();
  const day = now.getDay();
  const diff = now.getDate() - day + (day === 0 ? -6 : 1);
  const monday = new Date(now.getFullYear(), now.getMonth(), diff);
  monday.setHours(0, 0, 0, 0);
  const friday = new Date(monday);
  friday.setDate(monday.getDate() + 4);
  return {
    start: monday.toISOString().slice(0, 10),
    end: friday.toISOString().slice(0, 10),
  };
}

const HOURS = Array.from({ length: 10 }, (_, i) => i + 9);
const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"];

export default function CalendarView({ team }: { team: Team }) {
  const [loading, setLoading] = useState(false);
  const [slots, setSlots] = useState<Array<{ start: string; end: string; display: string }>>([]);
  const [message, setMessage] = useState("");
  const [booking, setBooking] = useState<{ title: string; slot: { start: string; display: string }; duration: number } | null>(null);
  const [range, setRange] = useState(getWeekRange());

  const fetchSlots = async () => {
    setLoading(true);
    setMessage("");
    try {
      const result = await findAvailability(
        team.id,
        range.start,
        range.end,
        30
      );
      setSlots(result.slots || []);
      setMessage(result.message || "");
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Failed to load availability");
      setSlots([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSlots();
  }, [team.id, range.start, range.end]);

  const handleBook = async () => {
    if (!booking) return;
    try {
      await bookMeeting(team.id, booking.title, booking.slot.start, booking.duration);
      setBooking(null);
      fetchSlots();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Booking failed");
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold flex items-center gap-2">
          <Calendar className="w-4 h-4" />
          Team Availability
        </h3>
        <div className="flex items-center gap-2 text-sm text-zinc-500">
          <span>{range.start}</span>
          <span>–</span>
          <span>{range.end}</span>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-violet-500" />
        </div>
      ) : (
        <div className="space-y-4">
          {message && (
            <div className="rounded-xl border border-zinc-700 bg-zinc-800/30 px-4 py-3 text-sm text-zinc-300">
              {message}
            </div>
          )}
          {slots.length > 0 && (
            <div className="space-y-2">
              <p className="text-sm text-zinc-500">Click a slot to book a meeting:</p>
              <div className="grid gap-2">
                {slots.slice(0, 8).map((slot, i) => (
                  <button
                    key={i}
                    onClick={() =>
                      setBooking({
                        title: "Team standup",
                        slot,
                        duration: 30,
                      })
                    }
                    className="flex items-center gap-3 rounded-xl border border-green-500/20 bg-green-500/5 px-4 py-3 text-left text-sm text-zinc-300 hover:border-green-500/40 hover:bg-green-500/10"
                  >
                    <Clock className="w-4 h-4 text-green-500" />
                    {slot.display}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {booking && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-zinc-900 rounded-2xl border border-zinc-700 p-6 max-w-md w-full space-y-4">
            <h3 className="font-semibold">Book Meeting</h3>
            <p className="text-sm text-zinc-400">{booking.slot.display}</p>
            <input
              type="text"
              placeholder="Meeting title"
              value={booking.title}
              onChange={(e) => setBooking({ ...booking, title: e.target.value })}
              className="w-full rounded-xl bg-zinc-800 border border-zinc-700 px-4 py-2 text-zinc-100"
            />
            <div className="flex gap-2">
              <button
                onClick={() => setBooking(null)}
                className="flex-1 rounded-xl border border-zinc-700 py-2 text-sm text-zinc-400"
              >
                Cancel
              </button>
              <button
                onClick={handleBook}
                className="flex-1 rounded-xl bg-violet-600 py-2 text-sm font-medium text-white"
              >
                Book
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
