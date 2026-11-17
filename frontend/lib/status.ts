export type ApiState = "checking" | "online" | "offline";

/** Maps a /health/ready HTTP outcome (null = not yet known) to a display state. */
export function toApiState(ok: boolean | null): ApiState {
  if (ok === null) return "checking";
  return ok ? "online" : "offline";
}
