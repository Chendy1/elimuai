"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { api } from "@/lib/api";
import { GENERIC_ERROR } from "@/lib/errors";
import { validateEmail, validateName, validatePassword } from "@/lib/validation";
import Field from "./Field";
import FormFeedback from "./FormFeedback";
import SubmitButton from "./SubmitButton";

export default function RegisterForm() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    const problem = validateName(name) ?? validateEmail(email) ?? validatePassword(password, email);
    if (problem) {
      setError(problem);
      return;
    }
    setBusy(true);
    const created = await api("/auth/register", {
      method: "POST",
      body: { email: email.trim(), password, display_name: name.trim() },
    });
    if (!created.ok) {
      setError(
        created.status === 409
          ? "We could not create an account with these details. If you already have one, please sign in."
          : (created.error ?? GENERIC_ERROR),
      );
      setBusy(false);
      return;
    }
    const session = await api("/auth/login", { method: "POST", body: { email: email.trim(), password } });
    setBusy(false);
    router.push(session.ok ? "/account" : "/login");
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4" noValidate>
      <Field id="name" label="Your name" value={name} onChange={setName} autoComplete="name" />
      <Field id="email" label="Email" type="email" value={email} onChange={setEmail} autoComplete="email" />
      <Field
        id="password"
        label="Password"
        type="password"
        value={password}
        onChange={setPassword}
        autoComplete="new-password"
        hint="At least 10 characters. A few random words make a strong password."
      />
      <FormFeedback error={error} />
      <SubmitButton busy={busy}>Create account</SubmitButton>
      <p className="text-center text-sm text-muted">
        Already have an account?{" "}
        <Link href="/login" className="font-semibold text-forest underline">
          Sign in
        </Link>
      </p>
    </form>
  );
}
