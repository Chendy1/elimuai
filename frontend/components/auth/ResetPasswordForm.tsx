"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useState, type FormEvent } from "react";
import { api } from "@/lib/api";
import { GENERIC_ERROR } from "@/lib/errors";
import { validatePassword } from "@/lib/validation";
import Field from "./Field";
import FormFeedback from "./FormFeedback";
import SubmitButton from "./SubmitButton";

export default function ResetPasswordForm() {
  const token = useSearchParams().get("token") ?? "";
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);

  if (!token) {
    return (
      <p className="text-muted">
        This reset link is incomplete.{" "}
        <Link href="/forgot-password" className="font-semibold text-forest underline">
          Request a new one
        </Link>
        .
      </p>
    );
  }

  if (done) {
    return (
      <div className="space-y-4">
        <FormFeedback success="Your password has been changed. You can now sign in." />
        <Link href="/login" className="font-semibold text-forest underline">
          Go to sign in
        </Link>
      </div>
    );
  }

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    const problem = validatePassword(password);
    if (problem) {
      setError(problem);
      return;
    }
    setBusy(true);
    const result = await api("/auth/password-reset/confirm", {
      method: "POST",
      body: { token, new_password: password },
    });
    setBusy(false);
    if (!result.ok) {
      setError(result.error ?? GENERIC_ERROR);
      return;
    }
    setDone(true);
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4" noValidate>
      <Field
        id="password"
        label="New password"
        type="password"
        value={password}
        onChange={setPassword}
        autoComplete="new-password"
        hint="At least 10 characters."
      />
      <FormFeedback error={error} />
      <SubmitButton busy={busy}>Change password</SubmitButton>
    </form>
  );
}
