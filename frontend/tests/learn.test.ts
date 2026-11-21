import { describe, expect, it } from "vitest";
import { attribution, learnHref, previewQuery, queryString } from "../lib/learn";

describe("learn helpers", () => {
  it("builds query strings and skips empty values", () => {
    expect(queryString({ a: "1", b: "", c: null, d: undefined, e: "x y" })).toBe("?a=1&e=x%20y");
    expect(queryString({})).toBe("");
  });
  it("only adds a version when previewing", () => {
    expect(previewQuery(null)).toBe("");
    expect(previewQuery("v1")).toBe("?version_id=v1");
  });
  it("keeps the preview and learner context in links", () => {
    expect(learnHref("/learn/area/a1", { version: "v1", learner: "l1" })).toBe("/learn/area/a1?version=v1&learner=l1");
    expect(learnHref("/learn", {})).toBe("/learn");
  });
  it("formats the source line", () => {
    expect(attribution([{ title: "Demo design", publisher: "Demo publisher" }])).toEqual(["Demo publisher, Demo design"]);
  });
});
