"use client";

import { useState, type FormEvent } from "react";
import Field from "@/components/auth/Field";
import FormFeedback from "@/components/auth/FormFeedback";
import SubmitButton from "@/components/auth/SubmitButton";
import { api } from "@/lib/api";
import { GENERIC_ERROR } from "@/lib/errors";
import type { ConsentNotice, Learner } from "@/lib/types";
import { validateNickname } from "@/lib/validation";
import GradeSelect from "./GradeSelect";

export default function AddLearnerForm({
  csrf,
  notice,
  onAdded,
}: {
  csrf: string;
  notice: ConsentNotice;
  onAdded: () => void;
}) {
  const [nickname, setNickname] = useState("");
  const [grade, setGrade] = useState("4");
  const [agreed, setAgreed] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    setSuccess("");
    const problem = validateNickname(nickname);
    if (problem) {
      setError(problem);
      return;
    }
    if (!agreed) {
      setError("Please tick the box to confirm consent.");
      return;
    }
    setBusy(true);
    const r = await api<Learner>("/learners", {
      method: "POST",
      csrf,
      body: {
        nickname: nickname.trim(),
        grade: Number(grade),
        consent: { notice_version: notice.version, accepted: true },
      },
    });
    setBusy(false);
    if (!r.ok) {
      setError(r.error ?? GENERIC_ERROR);
      return;
    }
    setNickname("");
    setAgreed(false);
    setSuccess("Learner added.");
    onAdded();
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4" noValidate>
      <Field
        id="learner-nickname"
        label="Learner nickname"
        value={nickname}
        onChange={setNickname}
        hint="A nickname only. Please do not use full names, email addresses or phone numbers."
      />
      <GradeSelect id="learner-grade" label="Learner grade" value={grade} onChange={setGrade} />

      <section aria-labelledby="notice-title" className="rounded-xl border-2 border-sage p-4">
        <h3 id="notice-title" className="font-bold text-forest">
          {notice.title}
        </h3>
        {notice.is_draft ? (
          <p className="mt-1 inline-block rounded-full bg-gold/30 px-3 py-1 text-xs font-semibold text-deep">
            Draft placeholder, not the final legal notice
          </p>
        ) : null}
        <p className="mt-3 max-h-48 overflow-y-auto whitespace-pre-line text-sm text-muted">{notice.text}</p>
      </section>

      <label className="flex items-start gap-3 text-sm text-ink">
        <input
          type="checkbox"
          checked={agreed}
          onChange={(e) => setAgreed(e.target.checked)}
          className="mt-1 h-5 w-5"
        />
        <span>{"I am this learner's parent or legal guardian and I agree to the consent notice above."}</span>
      </label>

      <FormFeedback error={error} success={success} />
      <SubmitButton busy={busy}>Add learner</SubmitButton>
    </form>
  );
}
