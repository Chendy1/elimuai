"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { GENERIC_ERROR } from "@/lib/errors";
import type { ConsentNotice, Learner, SessionData } from "@/lib/types";
import AddLearnerForm from "./AddLearnerForm";
import LearnerCard from "./LearnerCard";

export default function LearnersPanel() {
  const router = useRouter();
  const [csrf, setCsrf] = useState<string | null>(null);
  const [learners, setLearners] = useState<Learner[] | null>(null);
  const [notice, setNotice] = useState<ConsentNotice | null>(null);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    const r = await api<Learner[]>("/learners");
    if (r.ok && r.data) setLearners(r.data);
    else setError(r.error ?? GENERIC_ERROR);
  }, []);

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
      const [list, n] = await Promise.all([
        api<Learner[]>("/learners"),
        api<ConsentNotice>("/learners/consent-notice"),
      ]);
      if (cancelled) return;
      if (list.ok && list.data) setLearners(list.data);
      else setError(list.error ?? GENERIC_ERROR);
      if (n.ok && n.data) setNotice(n.data);
    })();
    return () => {
      cancelled = true;
    };
  }, [router]);

  if (error && learners === null) return <p className="text-red-800">{error}</p>;
  if (learners === null || csrf === null) return <p className="text-muted">Loading your learners...</p>;

  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-3xl font-bold text-forest">Your learners</h1>
        <p className="mt-1 text-muted">
          Add the children you look after. Each profile needs your consent.{" "}
          <Link href="/account" className="font-semibold text-forest underline">
            Back to your account
          </Link>
        </p>
      </div>

      {learners.length === 0 ? (
        <p className="rounded-xl bg-sage px-4 py-3 text-deep">No learners yet. Add the first one below.</p>
      ) : (
        <ul aria-label="Your learners" className="space-y-3">
          {learners.map((l) => (
            <li key={l.id} className="rounded-2xl bg-white p-5 shadow-card">
              <LearnerCard learner={l} csrf={csrf} onChanged={refresh} />
            </li>
          ))}
        </ul>
      )}

      <section aria-labelledby="add-title" className="rounded-2xl bg-white p-6 shadow-card">
        <h2 id="add-title" className="mb-4 text-2xl font-bold text-forest">
          Add a learner
        </h2>
        {notice ? (
          <AddLearnerForm csrf={csrf} notice={notice} onAdded={refresh} />
        ) : (
          <p className="text-muted">The consent notice could not be loaded. Please reload the page.</p>
        )}
      </section>
    </div>
  );
}
