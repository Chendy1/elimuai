import { describe, expect, it } from "vitest";
import { validateEmail, validateName, validatePassword } from "../lib/validation";

describe("validation", () => {
  it("requires a name", () => {
    expect(validateName("   ")).not.toBeNull();
    expect(validateName("Amina")).toBeNull();
  });
  it("checks email shape", () => {
    expect(validateEmail("nope")).not.toBeNull();
    expect(validateEmail("a@b.co")).toBeNull();
  });
  it("enforces password length", () => {
    expect(validatePassword("short")).toMatch(/at least 10/);
    expect(validatePassword("x".repeat(129))).toMatch(/128/);
    expect(validatePassword("correct-horse-battery")).toBeNull();
  });
  it("rejects a password equal to the email", () => {
    expect(validatePassword("guardian@example.com", "Guardian@Example.com")).not.toBeNull();
  });
});
