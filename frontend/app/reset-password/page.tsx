import type { Metadata } from "next";
import { Suspense } from "react";
import FormShell from "@/components/auth/FormShell";
import ResetPasswordForm from "@/components/auth/ResetPasswordForm";

export const metadata: Metadata = { title: "Choose a new password", robots: { index: false } };

export default function Page() {
  return (
    <FormShell title="Choose a new password">
      <Suspense fallback={<p className="text-muted">Loading...</p>}>
        <ResetPasswordForm />
      </Suspense>
    </FormShell>
  );
}
