import type { AreaNode, ReviewStatus, StrandNode, SubStrandNode, VersionTree } from "./types";

export const REVIEW_ROLES = ["content_reviewer", "curriculum_admin", "super_admin"];
export const PUBLISH_ROLES = ["curriculum_admin", "super_admin"];

export function hasAnyRole(roles: string[] | undefined, allowed: string[]): boolean {
  return (roles ?? []).some((r) => allowed.includes(r));
}

export type NodeKind = "learning_area" | "strand" | "sub_strand";
export type Selection = { kind: NodeKind; id: string };
export type Found = { area: AreaNode; strand?: StrandNode; sub?: SubStrandNode };

/** Active (non-archived) learning areas only: archived ones are ignored by publishing too. */
export function activeAreas(tree: VersionTree): AreaNode[] {
  return tree.grades.flatMap((g) => g.learning_areas).filter((a) => !a.archived);
}

export function statusCounts(tree: VersionTree): Record<ReviewStatus, number> {
  const counts: Record<ReviewStatus, number> = { draft: 0, in_review: 0, approved: 0, rejected: 0 };
  for (const area of activeAreas(tree))
    for (const strand of area.strands) for (const sub of strand.sub_strands) counts[sub.review_status] += 1;
  return counts;
}

export function pendingCounts(tree: VersionTree): { learning_area: number; strand: number; sub_strand: number } {
  const pending = { learning_area: 0, strand: 0, sub_strand: 0 };
  for (const area of activeAreas(tree)) {
    if (area.review_status !== "approved") pending.learning_area += 1;
    for (const strand of area.strands) {
      if (strand.review_status !== "approved") pending.strand += 1;
      for (const sub of strand.sub_strands) if (sub.review_status !== "approved") pending.sub_strand += 1;
    }
  }
  return pending;
}

export function findSelection(tree: VersionTree, sel: Selection | null): Found | null {
  if (!sel) return null;
  for (const area of tree.grades.flatMap((g) => g.learning_areas)) {
    if (sel.kind === "learning_area" && area.id === sel.id) return { area };
    for (const strand of area.strands) {
      if (sel.kind === "strand" && strand.id === sel.id) return { area, strand };
      for (const sub of strand.sub_strands)
        if (sel.kind === "sub_strand" && sub.id === sel.id) return { area, strand, sub };
    }
  }
  return null;
}

export const STATUS_LABEL: Record<ReviewStatus, string> = {
  draft: "Draft",
  in_review: "In review",
  approved: "Approved",
  rejected: "Needs changes",
};
