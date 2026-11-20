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
  it("explains a failed publish with its details", () => {
    const body = { detail: { message: "All content must be approved before publishing.", details: { unapproved: { learning_area: 0, strand: 2, sub_strand: 5 } } } };
    expect(errorMessage(body, 409)).toBe("All content must be approved before publishing. Still to approve: 2 strand, 5 sub strand.");
    const lic = { detail: { message: "Every source must have written permission recorded as granted.", details: { sources: ["Demo design"] } } };
    expect(errorMessage(lic, 409)).toContain("Sources: Demo design.");
  });
  it("falls back to a generic message", () => {
    expect(errorMessage(null, 500)).toBe(GENERIC_ERROR);
  });
});
