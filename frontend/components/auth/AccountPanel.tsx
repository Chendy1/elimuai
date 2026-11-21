"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { hasAnyRole, REVIEW_ROLES } from "@/lib/curriculumTree";
import type { SessionData } from "@/lib/types";

export default function AccountPanel() {
  const router = useRouter();
  const [session, setSession] = useState<SessionData | null>(null);

  useEffect(() => {
    let cancelled = false;
    api<SessionData>("/auth/me").then((r) => {
      if (cancelled) return;
      if (r.ok && r.data) setSession(r.data);
      else router.replace("/login");
    });
    return () => {
      cancelled = true;
    };
  }, [router]);

  async function signOut() {
    if (session) await api("/auth/logout", { method: "POST", csrf: session.csrf_token });
    router.replace("/login");
  }

  if (!session) return <p className="text-muted">Loading your account...</p>;

  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-bold text-forest">Welcome, {session.user.display_name}</h1>
      <p className="text-muted">Signed in as {session.user.email}.</p>
      <p className="rounded-xl bg-sage px-4 py-3 text-deep">
        Your guardian account is ready. You can add learners now. Starting lessons is coming soon.
      </p>
      <p>
        <Link href="/learn" className="font-semibold text-forest underline">
          Start learning
        </Link>
      </p>
      <p>
        <Link href="/learners" className="font-semibold text-forest underline">
          Manage your learners
        </Link>
      </p>
      {hasAnyRole(session.roles, REVIEW_ROLES) ? (
        <p>
          <Link href="/admin/curriculum" className="font-semibold text-forest underline">
            Curriculum review
          </Link>
        </p>
      ) : null}
      <button
        type="button"
        onClick={signOut}
        className="rounded-full border-2 border-forest px-6 py-3 font-semibold text-forest hover:bg-sage"
      >
        Sign out
      </button>
    </div>
  );
}
