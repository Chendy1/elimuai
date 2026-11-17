import { describe, expect, it } from "vitest";
import { toApiState } from "../lib/status";

describe("toApiState", () => {
  it("is checking before a result", () => expect(toApiState(null)).toBe("checking"));
  it("is online when ok", () => expect(toApiState(true)).toBe("online"));
  it("is offline when not ok", () => expect(toApiState(false)).toBe("offline"));
});
