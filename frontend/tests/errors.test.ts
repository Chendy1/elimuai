import { describe, expect, it } from "vitest";
import { errorMessage, GENERIC_ERROR } from "../lib/errors";

describe("errorMessage", () => {
  it("uses string details", () => {
    expect(errorMessage({ detail: "Invalid email or password." }, 401)).toBe("Invalid email or password.");
  });
  it("explains rate limiting", () => {
    expect(errorMessage({ detail: "x" }, 429)).toMatch(/Too many attempts/);
  });
  it("cleans validation errors", () => {
    const body = { detail: [{ loc: ["body"], msg: "Value error, Password must be 10 to 128 characters long." }] };
    expect(errorMessage(body, 422)).toBe("Password must be 10 to 128 characters long.");
  });
  it("maps email validation errors", () => {
    const body = { detail: [{ loc: ["body", "email"], msg: "value is not a valid email address" }] };
    expect(errorMessage(body, 422)).toBe("Please enter a valid email address.");
  });
  it("falls back to a generic message", () => {
    expect(errorMessage(null, 500)).toBe(GENERIC_ERROR);
  });
});
