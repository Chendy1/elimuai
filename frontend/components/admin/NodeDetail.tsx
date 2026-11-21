"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { GENERIC_ERROR } from "@/lib/errors";
import type { Found, NodeKind } from "@/lib/curriculumTree";
import type { ReviewStatus } from "@/lib/types";
import StatusBadge from "./StatusBadge";
import SourcePanel from "./SourcePanel";
import SubStrandEditor from "./SubStrandEditor";

function List({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) return null;
  return (
    <div>
      <h4 className="text-sm font-bold text-forest">{title}</h4>
      <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-ink">
        {items.map((t, i) => (
          <li key={i} className="whitespace-pre-line">
            {t}
          </li>
        ))}
      </ul>
    </div>
  );
}

const BUTTON = "rounded-full px-4 py-2 text-sm font-semibold disabled:opacity-60";

export default function NodeDetail({
  kind,
  found,
  csrf,
  canReview,
  canEdit,
  readOnly,
  onReviewed,
}: {
  kind: NodeKind;
  found: Found;
  csrf: string;
  canReview: boolean;
  canEdit: boolean;
  readOnly: boolean;
  onReviewed: () => void;
}) {
  const node = kind === "sub_strand" ? found.sub! : kind === "strand" ? found.strand! : found.area;
  const [comment, setComment] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState(false);

  const title =
    kind === "sub_strand"
      ? `${found.sub!.number} ${found.sub!.name}`
      : kind === "strand"
        ? `Strand ${found.strand!.number} ${found.strand!.name}`
        : found.area.name;

  async function review(status: ReviewStatus) {
    setBusy(true);
    setError("");
    const body: Record<string, unknown> = { kind, id: node.id, status };
    if (comment.trim()) body.comment = comment.trim();
    const r = await api("/admin/curriculum/review", { method: "POST", csrf, body });
    setBusy(false);
    if (!r.ok) {
      setError(r.error ?? GENERIC_ERROR);
      return;
    }
    setComment("");
    onReviewed();
  }

  const sub = found.sub;
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="text-2xl font-bold text-forest">{title}</h2>
        <StatusBadge status={node.review_status} testId="detail-status" />
      </div>

      {node.review_comment ? (
        <div className="rounded-xl bg-sage/60 px-4 py-3">
          <h3 className="text-sm font-bold text-deep">Notes (importer and earlier reviews)</h3>
          <p className="mt-1 whitespace-pre-line text-sm text-ink">{node.review_comment}</p>
        </div>
      ) : null}

      {sub && canEdit && !readOnly && !editing ? (
        <button type="button" onClick={() => setEditing(true)}
          className="rounded-full border-2 border-forest px-4 py-2 text-sm font-semibold text-forest hover:bg-sage">
          Edit record
        </button>
      ) : null}

      {sub && editing ? (
        <SubStrandEditor sub={sub} csrf={csrf} onCancel={() => setEditing(false)}
          onSaved={() => { setEditing(false); onReviewed(); }} />
      ) : null}

      {sub && !editing ? (
        <div className="space-y-4 rounded-xl bg-white p-5 shadow-card">
          <p className="text-sm text-muted">
            {sub.suggested_lessons !== null ? `${sub.suggested_lessons} suggested lessons` : "Lesson count not found"}
          </p>
          <List title="Topics" items={sub.topics} />
          <List title="Specific learning outcomes" items={sub.outcomes.map((o) => (o.code ? `${o.code}) ` : "") + o.text)} />
          <List title="Suggested learning experiences" items={sub.experiences} />
          <List title="Key inquiry questions" items={sub.inquiry_questions} />
          <List title="Core competencies" items={sub.competencies.map((c) => `${c.name}: ${c.description ?? ""}`)} />
          <List title="Values" items={sub.values.map((v) => `${v.name}: ${v.description ?? ""}`)} />
          <List title="Pertinent and contemporary issues" items={sub.pcis.map((p) => `${p.name}: ${p.description ?? ""}`)} />
          {sub.link_to_other_areas ? <List title="Link to other learning areas" items={[sub.link_to_other_areas]} /> : null}
        </div>
      ) : null}

      {kind === "strand" && found.strand!.rubric.length > 0 ? (
        <div className="space-y-2 rounded-xl bg-white p-5 shadow-card">
          <h4 className="text-sm font-bold text-forest">{`Assessment rubric (${found.strand!.rubric.length} indicators)`}</h4>
          <ul className="space-y-2 text-sm text-ink">
            {found.strand!.rubric.map((r, i) => (
              <li key={i}>{r.indicator}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {kind === "learning_area" ? (
        <p className="text-sm text-muted">
          Approve the learning area itself after its strands and sub-strands. Publishing needs every one approved.
        </p>
      ) : null}

      {canReview && !readOnly ? (
        <section aria-label="Review" className="space-y-3 rounded-xl border-2 border-sage p-4">
          <label htmlFor="review-comment" className="block text-sm font-semibold text-ink">
            Comment (optional)
          </label>
          <textarea
            id="review-comment"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            rows={3}
            className="w-full rounded-xl border-2 border-sage px-3 py-2 text-sm"
          />
          <div aria-live="assertive">{error ? <p className="text-sm text-red-800">{error}</p> : null}</div>
          <div className="flex flex-wrap gap-2">
            <button type="button" disabled={busy} onClick={() => review("approved")} className={`${BUTTON} bg-forest text-white hover:bg-deep`}>
              Approve
            </button>
            <button type="button" disabled={busy} onClick={() => review("rejected")} className={`${BUTTON} border-2 border-red-700 text-red-800`}>
              Needs changes
            </button>
            <button type="button" disabled={busy} onClick={() => review("in_review")} className={`${BUTTON} border-2 border-forest text-forest`}>
              Mark in review
            </button>
          </div>
        </section>
      ) : null}

      {kind !== "learning_area" ? <SourcePanel key={node.source_page_id ?? "none"} pageId={node.source_page_id} /> : null}
    </div>
  );
}
