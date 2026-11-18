import { describe, expect, it } from "vitest";
import { validateNickname } from "../lib/validation";

describe("validateNickname", () => {
  it("accepts ordinary nicknames", () => {
    expect(validateNickname("Zuri")).toBeNull();
    expect(validateNickname("Kid1")).toBeNull();
  });
  it("rejects empty and over-long values", () => {
    expect(validateNickname("   ")).not.toBeNull();
    expect(validateNickname("x".repeat(51))).not.toBeNull();
  });
  it("rejects email addresses and phone-like numbers", () => {
    expect(validateNickname("kid@example.com")).not.toBeNull();
    expect(validateNickname("0712345678")).not.toBeNull();
  });
});
