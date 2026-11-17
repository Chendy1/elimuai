export const GENERIC_ERROR = "Something went wrong. Please try again.";

/** Turns an API error body into one friendly sentence. */
export function errorMessage(data: unknown, status: number): string {
  if (status === 429) return "Too many attempts. Please wait a few minutes and try again.";
  if (data && typeof data === "object" && "detail" in data) {
    const detail = (data as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0] as { msg?: unknown; loc?: unknown };
      const loc = Array.isArray(first.loc) ? first.loc.map(String) : [];
      if (loc.includes("email")) return "Please enter a valid email address.";
      if (typeof first.msg === "string") return first.msg.replace(/^Value error, /, "");
    }
  }
  return GENERIC_ERROR;
}
