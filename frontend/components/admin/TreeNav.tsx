import type { Selection } from "@/lib/curriculumTree";
import type { VersionTree } from "@/lib/types";
import StatusBadge from "./StatusBadge";

function row(active: boolean, indent: string) {
  return `flex w-full items-center justify-between gap-2 rounded-lg px-2 py-2 text-left text-sm ${indent} ${
    active ? "bg-sage font-semibold text-deep" : "text-ink hover:bg-sage/60"
  }`;
}

export default function TreeNav({
  tree,
  selection,
  onSelect,
}: {
  tree: VersionTree;
  selection: Selection | null;
  onSelect: (s: Selection) => void;
}) {
  return (
    <nav aria-label="Curriculum structure" className="space-y-4">
      {tree.grades.map((grade) => (
        <div key={grade.id}>
          <p className="px-2 text-xs font-bold uppercase tracking-wide text-muted">{grade.name}</p>
          {grade.learning_areas.map((area) => (
            <div key={area.id} className="mt-1">
              <button
                type="button"
                onClick={() => onSelect({ kind: "learning_area", id: area.id })}
                className={row(selection?.id === area.id, "")}
              >
                <span>{area.name + (area.archived ? " (archived)" : "")}</span>
                <StatusBadge status={area.review_status} />
              </button>
              {area.strands.map((strand) => (
                <div key={strand.id}>
                  <button
                    type="button"
                    onClick={() => onSelect({ kind: "strand", id: strand.id })}
                    className={row(selection?.id === strand.id, "ml-3")}
                  >
                    <span>{"Strand " + strand.number + " " + strand.name}</span>
                    <StatusBadge status={strand.review_status} />
                  </button>
                  {strand.sub_strands.map((sub) => (
                    <button
                      key={sub.id}
                      type="button"
                      onClick={() => onSelect({ kind: "sub_strand", id: sub.id })}
                      className={row(selection?.id === sub.id, "ml-6")}
                    >
                      <span>{sub.number + " " + sub.name}</span>
                      <StatusBadge status={sub.review_status} />
                    </button>
                  ))}
                </div>
              ))}
            </div>
          ))}
        </div>
      ))}
    </nav>
  );
}
