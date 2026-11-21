import { describe, expect, it } from "vitest";
import {
  formatCompetencies, formatNamed, formatOutcomes, parseBlocks, parseCompetencies, parseLines,
  parseNamed, parseOutcomes,
} from "../lib/editParse";

describe("edit form parsing", () => {
  it("splits lines and drops blanks", () => {
    expect(parseLines(" one \n\n two\n")).toEqual(["one", "two"]);
  });
  it("splits blocks on blank lines and keeps inner line breaks", () => {
    expect(parseBlocks("first item\n- nested\n\nsecond item")).toEqual(["first item\n- nested", "second item"]);
  });
  it("reads outcome letters when present", () => {
    expect(parseOutcomes("a) first\nsecond without a letter\nc)   third")).toEqual([
      { code: "a", text: "first" },
      { code: null, text: "second without a letter" },
      { code: "c", text: "third" },
    ]);
  });
  it("splits names from descriptions at the first colon", () => {
    expect(parseNamed("Unity: works together: always\nSafety")).toEqual([
      { name: "Unity", description: "works together: always" },
      { name: "Safety", description: null },
    ]);
  });
  it("maps competency names to codes and reports unknown ones", () => {
    const r = parseCompetencies("Self -efficacy: confident\ncritical thinking and problem solving: demo\nMade up: x");
    expect(r.items.map((i) => i.code)).toEqual(["self_efficacy", "critical_thinking"]);
    expect(r.unknown).toEqual(["Made up"]);
  });
  it("round-trips through the formatters", () => {
    expect(parseOutcomes(formatOutcomes([{ code: "a", text: "x" }, { code: null, text: "y" }]))).toEqual([
      { code: "a", text: "x" }, { code: null, text: "y" },
    ]);
    expect(parseNamed(formatNamed([{ name: "Unity", description: "d" }]))).toEqual([{ name: "Unity", description: "d" }]);
    expect(parseCompetencies(formatCompetencies([{ code: "citizenship", description: null }])).items).toEqual([
      { code: "citizenship", description: null },
    ]);
  });
});
