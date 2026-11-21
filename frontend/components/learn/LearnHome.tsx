"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { GENERIC_ERROR } from "@/lib/errors";
import { hasAnyRole, REVIEW_ROLES } from "@/lib/curriculumTree";
import { learnHref, previewQuery, type LearnArea } from "@/lib/learn";
import type { Learner, SessionData } from "@/lib/types";

const GRADES = [4, 5, 6, 7, 8, 9];

export default function LearnHome() {
  const router = useRouter();
  const params = useSearchParams();
  const version = params.get("version");
  const gradeParam = params.get("grade");
  const learnerParam = params.get("learner");

  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [learners, setLearners] = useState<Learner[]>([]);
  const [learnerId, setLearnerId] = useState<string | null>(null);
  const [grade, setGrade] = useState<number | null>(null);
  const [areas, setAreas] = useState<LearnArea[] | null>(null);
  const [areasError, setAreasError] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const me = await api<SessionData>("/auth/me");
      if (cancelled) return;
      if (!me.ok || !me.data) {
        router.replace("/login");
        return;
      }
      if (version) {
        if (!hasAnyRole(me.data.roles, REVIEW_ROLES)) {
          setMessage("Only reviewers can preview an unpublished version.");
        } else {
          setGrade(Number(gradeParam) || 6);
        }
        setLoading(false);
        return;
      }
      const r = await api<Learner[]>("/learners");
      if (cancelled) return;
      if (!r.ok || !r.data) {
        setMessage("Learning is for guardians and their learners. Please sign in with a guardian account.");
      } else {
        setLearners(r.data);
        const chosen = r.data.find((l) => l.id === learnerParam) ?? r.data[0] ?? null;
        setLearnerId(chosen?.id ?? null);
        if (chosen) setGrade(chosen.grade);
      }
      setLoading(false);
    })();
    return () => {
      cancelled = true;
    };
  }, [router, version, gradeParam, learnerParam]);

  useEffect(() => {
    if (grade === null) return;
    let cancelled = false;
    api<LearnArea[]>(`/curriculum/grades/${grade}/learning-areas${previewQuery(version)}`).then((r) => {
      if (cancelled) return;
      if (r.ok && r.data) {
        setAreas(r.data);
        setAreasError("");
      } else if (r.status === 404) {
        setAreas([]);
        setAreasError("Lessons for this grade are not ready yet. Please check back soon.");
      } else {
        setAreasError(r.error ?? GENERIC_ERROR);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [grade, version]);

  if (loading) return <p className="text-muted">Loading...</p>;
  if (message) return <p className="rounded-xl bg-sage px-4 py-3 text-deep">{message}</p>;

  const learner = learners.find((l) => l.id === learnerId) ?? null;

  return (
    <div className="space-y-8">
      {version ? (
        <div className="rounded-xl bg-gold/20 px-4 py-3 text-sm text-deep">
          <p className="font-semibold">Staff preview</p>
          <p>This is how learners will see the version you are previewing. Learners cannot see it until it is published.</p>
          <label htmlFor="preview-grade" className="mt-2 block font-semibold">
            Grade
          </label>
          <select
            id="preview-grade"
            value={grade ?? 6}
            onChange={(e) => setGrade(Number(e.target.value))}
            className="mt-1 rounded-xl border-2 border-sage bg-white px-3 py-2"
          >
            {GRADES.map((g) => (
              <option key={g} value={g}>
                {"Grade " + g}
              </option>
            ))}
          </select>
        </div>
      ) : learner ? (
        <div>
          <h1 className="text-3xl font-bold text-forest">{"Hello, " + learner.nickname + "!"}</h1>
          <p className="mt-1 text-lg text-muted">{"Grade " + learner.grade + ". Choose a subject to start."}</p>
          {learners.length > 1 ? (
            <div className="mt-3">
              <label htmlFor="learner" className="block text-sm font-semibold text-ink">
                Learning as
              </label>
              <select
                id="learner"
                value={learner.id}
                onChange={(e) => router.replace(learnHref("/learn", { learner: e.target.value }))}
                className="mt-1 rounded-xl border-2 border-sage bg-white px-3 py-2"
              >
                {learners.map((l) => (
                  <option key={l.id} value={l.id}>
                    {l.nickname + " (Grade " + l.grade + ")"}
                  </option>
                ))}
              </select>
            </div>
          ) : null}
        </div>
      ) : (
        <div className="rounded-xl bg-sage px-4 py-3 text-deep">
          <p>Add a learner first, then come back to start learning.</p>
          <Link href="/learners" className="font-semibold text-forest underline">
            Add a learner
          </Link>
        </div>
      )}

      {version ? <h1 className="text-3xl font-bold text-forest">{"Grade " + (grade ?? 6) + " subjects"}</h1> : null}
      {areasError ? <p className="rounded-xl bg-sage px-4 py-3 text-deep">{areasError}</p> : null}
      {areas && areas.length === 0 && !areasError ? <p className="text-muted">No subjects here yet.</p> : null}
      {areas && areas.length > 0 ? (
        <ul aria-label="Subjects" className="grid gap-4 sm:grid-cols-2">
          {areas.map((a) => (
            <li key={a.id}>
              <Link
                href={learnHref(`/learn/area/${a.id}`, { version, learner: learnerId })}
                className="block rounded-2xl bg-white p-6 text-xl font-bold text-forest shadow-card hover:bg-sage"
              >
                {a.name}
              </Link>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
