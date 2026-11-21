"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { GENERIC_ERROR } from "@/lib/errors";
import {
  findSelection, hasAnyRole, pendingCounts, PUBLISH_ROLES, REVIEW_ROLES, statusCounts, type Selection,
} from "@/lib/curriculumTree";
import type { SessionData, VersionTree } from "@/lib/types";
import NodeDetail from "./NodeDetail";
import TreeNav from "./TreeNav";

export default function VersionReview({ versionId }: { versionId: string }) {
  const router = useRouter();
  const [csrf, setCsrf] = useState<string | null>(null);
  const [roles, setRoles] = useState<string[]>([]);
  const [tree, setTree] = useState<VersionTree | null>(null);
  const [selection, setSelection] = useState<Selection | null>(null);
  const [error, setError] = useState("");
  const [publishMessage, setPublishMessage] = useState("");
  const [publishError, setPublishError] = useState("");
  const [busy, setBusy] = useState(false);
  const [denied, setDenied] = useState(false);

  const refresh = useCallback(async () => {
    const r = await api<VersionTree>(`/admin/curriculum/versions/${versionId}/tree`);
    if (r.ok && r.data) setTree(r.data);
    else setError(r.error ?? GENERIC_ERROR);
  }, [versionId]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const me = await api<SessionData>("/auth/me");
      if (cancelled) return;
      if (!me.ok || !me.data) {
        router.replace("/login");
        return;
      }
      setCsrf(me.data.csrf_token);
      setRoles(me.data.roles ?? []);
      if (!hasAnyRole(me.data.roles, REVIEW_ROLES)) {
        setDenied(true);
        return;
      }
      const r = await api<VersionTree>(`/admin/curriculum/versions/${versionId}/tree`);
      if (cancelled) return;
      if (r.ok && r.data) setTree(r.data);
      else setError(r.error ?? GENERIC_ERROR);
    })();
    return () => {
      cancelled = true;
    };
  }, [router, versionId]);

  async function publish() {
    if (!csrf) return;
    setBusy(true);
    setPublishError("");
    setPublishMessage("");
    const r = await api(`/admin/curriculum/versions/${versionId}/publish`, { method: "POST", csrf, body: {} });
    setBusy(false);
    if (!r.ok) {
      setPublishError(r.error ?? GENERIC_ERROR);
      return;
    }
    setPublishMessage("Published. Learners can now see this version.");
    refresh();
  }

  if (denied) return <p className="rounded-xl bg-sage px-4 py-3 text-deep">Your account does not have access to curriculum review.</p>;
  if (error && !tree) return <p className="text-red-800">{error}</p>;
  if (!tree || csrf === null) return <p className="text-muted">Loading the curriculum...</p>;

  const counts = statusCounts(tree);
  const pending = pendingCounts(tree);
  const total = counts.draft + counts.in_review + counts.approved + counts.rejected;
  const found = findSelection(tree, selection);
  const readOnly = tree.status !== "draft";
  const canPublish = hasAnyRole(roles, PUBLISH_ROLES) && !readOnly;

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm">
          <Link href="/admin/curriculum" className="font-semibold text-forest underline">
            All curricula
          </Link>
        </p>
        <h1 className="mt-1 text-3xl font-bold text-forest">{"Review: " + tree.label}</h1>
        <p className="mt-1 text-muted">{"Version status: " + tree.status}</p>
      </div>

      {readOnly ? (
        <p className="rounded-xl bg-gold/20 px-4 py-3 text-sm text-deep">This version is {tree.status} and read-only. Create a new draft version to make changes.</p>
      ) : null}

      <section aria-label="Progress" className="flex flex-wrap items-center justify-between gap-4 rounded-xl bg-white p-4 shadow-card">
        <p data-testid="progress" className="text-sm text-ink">
          {`${counts.approved} of ${total} sub-strands approved. Still to approve: ${pending.learning_area} learning area, ${pending.strand} strand, ${pending.sub_strand} sub-strand.`}
        </p>
        {canPublish ? (
          <button type="button" disabled={busy} onClick={publish} className="rounded-full bg-forest px-5 py-2 text-sm font-semibold text-white hover:bg-deep disabled:opacity-60">
            Publish version
          </button>
        ) : null}
      </section>
      <div aria-live="assertive">
        {publishError ? <p className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-800">{publishError}</p> : null}
        {publishMessage ? <p className="rounded-xl bg-sage px-4 py-3 text-sm text-deep">{publishMessage}</p> : null}
      </div>

      <div className="grid gap-6 lg:grid-cols-[20rem_1fr]">
        <aside className="max-h-[75vh] overflow-y-auto rounded-xl bg-white p-3 shadow-card">
          <TreeNav tree={tree} selection={selection} onSelect={setSelection} />
        </aside>
        <div>
          {selection && found ? (
            <NodeDetail
              key={selection.id}
              kind={selection.kind}
              found={found}
              csrf={csrf}
              canReview={hasAnyRole(roles, REVIEW_ROLES)}
              canEdit={hasAnyRole(roles, PUBLISH_ROLES)}
              readOnly={readOnly}
              onReviewed={refresh}
            />
          ) : (
            <p className="rounded-xl bg-sage px-4 py-3 text-deep">Choose a learning area, strand or sub-strand on the left to review it.</p>
          )}
        </div>
      </div>
    </div>
  );
}
