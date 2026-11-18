"use client";

import { useState, type FormEvent } from "react";
import Field from "@/components/auth/Field";
import FormFeedback from "@/components/auth/FormFeedback";
import { api } from "@/lib/api";
import { GENERIC_ERROR } from "@/lib/errors";
import type { Learner } from "@/lib/types";
import { validateNickname } from "@/lib/validation";
import GradeSelect from "./GradeSelect";

const small = "rounded-full border-2 border-forest px-4 py-2 text-sm font-semibold text-forest hover:bg-sage";
const solid = "rounded-full bg-forest px-4 py-2 text-sm font-semibold text-white hover:bg-deep disabled:opacity-60";

export default function LearnerCard({
  learner,
  csrf,
  onChanged,
}: {
  learner: Learner;
  csrf: string;
  onChanged: () => void;
}) {
  const [mode, setMode] = useState<"view" | "edit" | "confirm">("view");
  const [nickname, setNickname] = useState(learner.nickname);
  const [grade, setGrade] = useState(String(learner.grade));
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function startEdit() {
    setNickname(learner.nickname);
    setGrade(String(learner.grade));
    setError("");
    setMode("edit");
  }

  async function save(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    const problem = validateNickname(nickname);
    if (problem) {
      setError(problem);
      return;
    }
    setBusy(true);
    const r = await api(`/learners/${learner.id}`, {
      method: "PATCH",
      csrf,
      body: { nickname: nickname.trim(), grade: Number(grade) },
    });
    setBusy(false);
    if (!r.ok) {
      setError(r.error ?? GENERIC_ERROR);
      return;
    }
    setMode("view");
    onChanged();
  }

  async function remove() {
    setBusy(true);
    const r = await api(`/learners/${learner.id}`, { method: "DELETE", csrf });
    setBusy(false);
    if (!r.ok) {
      setError(r.error ?? GENERIC_ERROR);
      setMode("view");
      return;
    }
    onChanged();
  }

  if (mode === "edit") {
    return (
      <form onSubmit={save} className="space-y-3" noValidate>
        <Field id={`edit-nickname-${learner.id}`} label="Edit nickname" value={nickname} onChange={setNickname} />
        <GradeSelect id={`edit-grade-${learner.id}`} label="Edit grade" value={grade} onChange={setGrade} />
        <FormFeedback error={error} />
        <div className="flex gap-2">
          <button type="submit" disabled={busy} className={solid}>
            Save
          </button>
          <button type="button" onClick={() => setMode("view")} className={small}>
            Cancel
          </button>
        </div>
      </form>
    );
  }

  if (mode === "confirm") {
    return (
      <div className="space-y-3">
        <p className="text-ink">
          {"Remove " + learner.nickname + "? This hides the profile and withdraws your consent."}
        </p>
        <div className="flex gap-2">
          <button type="button" onClick={remove} disabled={busy} className={solid}>
            Yes, remove
          </button>
          <button type="button" onClick={() => setMode("view")} className={small}>
            Keep
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div>
        <p className="text-lg font-bold text-forest">{learner.nickname}</p>
        <p className="text-muted">{"Grade " + learner.grade}</p>
        <FormFeedback error={error} />
      </div>
      <div className="flex gap-2">
        <button type="button" onClick={startEdit} className={small}>
          Edit
        </button>
        <button type="button" onClick={() => setMode("confirm")} className={small}>
          Remove
        </button>
      </div>
    </div>
  );
}
