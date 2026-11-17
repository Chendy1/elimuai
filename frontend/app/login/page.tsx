import type { Metadata } from "next";
import FormShell from "@/components/auth/FormShell";
import LoginForm from "@/components/auth/LoginForm";

export const metadata: Metadata = { title: "Sign in", robots: { index: false } };

export default function Page() {
  return (
    <FormShell title="Sign in" intro="Welcome back.">
      <LoginForm />
    </FormShell>
  );
}
