"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { api } from "@/lib/api";
import { GENERIC_ERROR } from "@/lib/errors";
import { validateEmail } from "@/lib/validation";
import Field from "./Field";
import FormFeedback from "./FormFeedback";
import SubmitButton from "./SubmitButton";

export default function LoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    const problem = validateEmail(email) ?? (password ? null : "Please enter your password.");
    if (problem) {
      setError(problem);
      return;
    }
    setBusy(true);
    const result = await api("/auth/login", { method: "POST", body: { email: email.trim(), password } });
    if (!result.ok) {
      setError(result.error ?? GENERIC_ERROR);
      setBusy(false);
      return;
    }
    router.push("/account");
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4" noValidate>
      <Field id="email" label="Email" type="email" value={email} onChange={setEmail} autoComplete="email" />
      <Field
        id="password"
        label="Password"
        type="password"
        value={password}
        onChange={setPassword}
        autoComplete="current-password"
      />
      <FormFeedback error={error} />
      <SubmitButton busy={busy}>Sign in</SubmitButton>
      <p className="text-center text-sm text-muted">
        <Link href="/forgot-password" className="font-semibold text-forest underline">
          Forgot your password?
        </Link>
      </p>
      <p className="text-center text-sm text-muted">
        New here?{" "}
        <Link href="/register" className="font-semibold text-forest underline">
          Create a guardian account
        </Link>
      </p>
    </form>
  );
}
