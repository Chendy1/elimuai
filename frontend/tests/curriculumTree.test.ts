import { describe, expect, it } from "vitest";
import { findSelection, hasAnyRole, pendingCounts, PUBLISH_ROLES, REVIEW_ROLES, statusCounts } from "../lib/curriculumTree";
import type { ReviewStatus, VersionTree } from "../lib/types";

function sub(id: string, status: ReviewStatus) {
  return {
    id, number: "1.1", name: "Demo", suggested_lessons: 1, link_to_other_areas: null, topics: [], outcomes: [],
    experiences: [], inquiry_questions: [], competencies: [], values: [], pcis: [],
    review_status: status, review_comment: null, source_page_id: null,
  };
}
const base = { review_comment: null, source_page_id: null };
const tree: VersionTree = {
  id: "v", label: "Demo", status: "draft",
  grades: [{
    id: "g", level: 6, name: "Grade 6",
    learning_areas: [
      { id: "a1", name: "Active", sort_order: 0, archived: false, review_status: "approved", ...base,
        strands: [{ id: "s1", number: "1.0", name: "S", unit_id: null, rubric: [], review_status: "draft", ...base,
          sub_strands: [sub("x1", "approved"), sub("x2", "draft"), sub("x3", "rejected")] }] },
      { id: "a2", name: "Archived", sort_order: 1, archived: true, review_status: "draft", ...base,
        strands: [{ id: "s2", number: "2.0", name: "S", unit_id: null, rubric: [], review_status: "draft", ...base,
          sub_strands: [sub("x4", "draft")] }] },
    ],
  }],
};

describe("curriculum tree helpers", () => {
  it("counts sub-strands by status and ignores archived areas", () => {
    expect(statusCounts(tree)).toEqual({ draft: 1, in_review: 0, approved: 1, rejected: 1 });
  });
  it("counts what still blocks publishing", () => {
    expect(pendingCounts(tree)).toEqual({ learning_area: 0, strand: 1, sub_strand: 2 });
  });
  it("finds a selected node and its parents", () => {
    const found = findSelection(tree, { kind: "sub_strand", id: "x2" });
    expect(found?.area.id).toBe("a1");
    expect(found?.strand?.id).toBe("s1");
    expect(found?.sub?.id).toBe("x2");
    expect(findSelection(tree, { kind: "strand", id: "nope" })).toBeNull();
    expect(findSelection(tree, null)).toBeNull();
  });
  it("checks roles", () => {
    expect(hasAnyRole(["guardian"], REVIEW_ROLES)).toBe(false);
    expect(hasAnyRole(["guardian", "content_reviewer"], REVIEW_ROLES)).toBe(true);
    expect(hasAnyRole(["content_reviewer"], PUBLISH_ROLES)).toBe(false);
    expect(hasAnyRole(undefined, REVIEW_ROLES)).toBe(false);
  });
});
