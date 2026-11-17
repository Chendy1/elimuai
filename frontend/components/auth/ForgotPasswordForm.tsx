"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";
import { api } from "@/lib/api";
import { GENERIC_ERROR } from "@/lib/errors";
import { validateEmail } from "@/lib/validation";
import Field from "./Field";
import FormFeedback from "./FormFeedback";
import SubmitButton from "./SubmitButton";

export default function ForgotPasswordForm() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    const problem = validateEmail(email);
    if (problem) {
      setError(problem);
      return;
    }
    setBusy(true);
    const result = await api("/auth/password-reset/request", { method: "POST", body: { email: email.trim() } });
    setBusy(false);
    if (!result.ok) {
      setError(result.error ?? GENERIC_ERROR);
      return;
    }
    setDone(true);
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4" noValidate>
      <Field id="email" label="Email" type="email" value={email} onChange={setEmail} autoComplete="email" />
      <FormFeedback
        error={error}
        success={done ? "If an account exists for that email, a reset link has been sent. It expires in 30 minutes." : undefined}
      />
      <SubmitButton busy={busy}>Send reset link</SubmitButton>
      <p className="text-center text-sm text-muted">
        <Link href="/login" className="font-semibold text-forest underline">
          Back to sign in
        </Link>
      </p>
    </form>
  );
}
