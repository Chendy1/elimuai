"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { attribution, learnHref, previewQuery, type LearnSubStrand, type LearnTree } from "@/lib/learn";

function Overview({ sub }: { sub: LearnSubStrand }) {
  return (
    <section aria-label="Topic overview" className="space-y-5 rounded-2xl bg-white p-6 shadow-card">
      <h2 className="text-2xl font-bold text-forest">{sub.number + " " + sub.name}</h2>
      {sub.suggested_lessons ? <p className="text-muted">{"About " + sub.suggested_lessons + " lessons"}</p> : null}
      {sub.outcomes.length > 0 ? (
        <div>
          <h3 className="text-lg font-bold text-deep">What you will learn</h3>
          <ul className="mt-2 list-disc space-y-1 pl-6 text-ink">
            {sub.outcomes.map((o, i) => (
              <li key={i}>{o.text}</li>
            ))}
          </ul>
        </div>
      ) : null}
      {sub.topics.length > 0 ? (
        <div>
          <h3 className="text-lg font-bold text-deep">Topics</h3>
          <ul className="mt-2 list-disc space-y-1 pl-6 text-ink">
            {sub.topics.map((t, i) => (
              <li key={i}>{t}</li>
            ))}
          </ul>
        </div>
      ) : null}
      {sub.inquiry_questions.length > 0 ? (
        <div>
          <h3 className="text-lg font-bold text-deep">Think about it</h3>
          <ul className="mt-2 list-disc space-y-1 pl-6 text-ink">
            {sub.inquiry_questions.map((q, i) => (
              <li key={i}>{q}</li>
            ))}
          </ul>
        </div>
      ) : null}
      <p className="rounded-xl bg-sage px-4 py-3 text-deep">Lessons for this topic are coming soon.</p>
    </section>
  );
}

export default function AreaView({ areaId }: { areaId: string }) {
  const router = useRouter();
  const params = useSearchParams();
  const version = params.get("version");
  const learner = params.get("learner");
  const [tree, setTree] = useState<LearnTree | null>(null);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<string | null>(params.get("sub"));

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const me = await api("/auth/me");
      if (cancelled) return;
      if (!me.ok) {
        router.replace("/login");
        return;
      }
      const r = await api<LearnTree>(`/curriculum/learning-areas/${areaId}${previewQuery(version)}`);
      if (cancelled) return;
      if (r.ok && r.data) setTree(r.data);
      else setError(r.status === 404 ? "This subject is not available." : (r.error ?? "Something went wrong."));
    })();
    return () => {
      cancelled = true;
    };
  }, [router, areaId, version]);

  if (error) return <p className="rounded-xl bg-sage px-4 py-3 text-deep">{error}</p>;
  if (!tree) return <p className="text-muted">Loading...</p>;

  const all = tree.strands.flatMap((s) => s.sub_strands);
  const current = all.find((s) => s.id === selected) ?? null;
  const back = learnHref("/learn", { version, learner });

  return (
    <div className="space-y-8">
      <div>
        <p className="text-sm">
          <Link href={back} className="font-semibold text-forest underline">
            Back to subjects
          </Link>
        </p>
        <h1 className="mt-1 text-3xl font-bold text-forest">{tree.name}</h1>
      </div>

      {version ? (
        <p className="rounded-xl bg-gold/20 px-4 py-3 text-sm text-deep">
          {"Staff preview of " + tree.version.label + " (" + tree.version.status + "). Learners cannot see this version yet."}
        </p>
      ) : null}

      <div className="grid gap-8 lg:grid-cols-[22rem_1fr]">
        <nav aria-label="Topics" className="space-y-5">
          {tree.strands.map((strand) => (
            <div key={strand.id}>
              <h2 className="text-sm font-bold uppercase tracking-wide text-muted">{"Strand " + strand.number + " " + strand.name}</h2>
              <ul className="mt-2 space-y-2">
                {strand.sub_strands.map((sub) => (
                  <li key={sub.id}>
                    <button
                      type="button"
                      onClick={() => setSelected(sub.id)}
                      className={`w-full rounded-xl px-4 py-3 text-left shadow-card ${
                        selected === sub.id ? "bg-sage text-deep" : "bg-white text-ink hover:bg-sage/60"
                      }`}
                    >
                      <span className="block font-semibold">{sub.number + " " + sub.name}</span>
                      {sub.suggested_lessons ? (
                        <span className="text-sm text-muted">{sub.suggested_lessons + " lessons"}</span>
                      ) : null}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>
        <div>
          {current ? (
            <Overview sub={current} />
          ) : (
            <p className="rounded-xl bg-sage px-4 py-3 text-deep">Choose a topic on the left to see what it covers.</p>
          )}
        </div>
      </div>

      {tree.sources.length > 0 ? (
        <p data-testid="attribution" className="text-sm text-muted">
          {"Curriculum source: " + attribution(tree.sources).join("; ") + ". ElimuAI is an independent project and is not endorsed by KICD."}
        </p>
      ) : null}
    </div>
  );
}
