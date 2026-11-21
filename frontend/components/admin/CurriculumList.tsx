"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { GENERIC_ERROR } from "@/lib/errors";
import { hasAnyRole, REVIEW_ROLES } from "@/lib/curriculumTree";
import type { CurriculumSummary, SessionData, VersionSummary } from "@/lib/types";

type Entry = { curriculum: CurriculumSummary; versions: VersionSummary[] };

export default function CurriculumList() {
  const router = useRouter();
  const [entries, setEntries] = useState<Entry[] | null>(null);
  const [denied, setDenied] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const me = await api<SessionData>("/auth/me");
      if (cancelled) return;
      if (!me.ok || !me.data) {
        router.replace("/login");
        return;
      }
      if (!hasAnyRole(me.data.roles, REVIEW_ROLES)) {
        setDenied(true);
        return;
      }
      const list = await api<CurriculumSummary[]>("/admin/curriculum/curricula");
      if (cancelled) return;
      if (!list.ok || !list.data) {
        setError(list.error ?? GENERIC_ERROR);
        return;
      }
      const out: Entry[] = [];
      for (const curriculum of list.data) {
        const v = await api<VersionSummary[]>(`/admin/curriculum/curricula/${curriculum.id}/versions`);
        out.push({ curriculum, versions: v.ok && v.data ? v.data : [] });
      }
      if (!cancelled) setEntries(out);
    })();
    return () => {
      cancelled = true;
    };
  }, [router]);

  if (denied) return <p className="rounded-xl bg-sage px-4 py-3 text-deep">Your account does not have access to curriculum review.</p>;
  if (error) return <p className="text-red-800">{error}</p>;
  if (entries === null) return <p className="text-muted">Loading...</p>;

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-forest">Curriculum review</h1>
      {entries.length === 0 ? (
        <p className="rounded-xl bg-sage px-4 py-3 text-deep">No curricula yet. Create one with the command line tool, then import and propose a source.</p>
      ) : null}
      {entries.map(({ curriculum, versions }) => (
        <section key={curriculum.id} className="rounded-2xl bg-white p-5 shadow-card">
          <h2 className="text-xl font-bold text-forest">{curriculum.name}</h2>
          <p className="text-sm text-muted">{curriculum.code}</p>
          <ul className="mt-3 space-y-2">
            {versions.map((v) => (
              <li key={v.id}>
                <Link href={`/admin/curriculum/${v.id}`} className="font-semibold text-forest underline">
                  {v.label}
                </Link>
                <span className="ml-2 text-sm text-muted">{v.status}</span>
              </li>
            ))}
            {versions.length === 0 ? <li className="text-sm text-muted">No versions yet.</li> : null}
          </ul>
        </section>
      ))}
    </div>
  );
}
