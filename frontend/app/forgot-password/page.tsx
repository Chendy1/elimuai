import type { Metadata } from "next";
import FormShell from "@/components/auth/FormShell";
import ForgotPasswordForm from "@/components/auth/ForgotPasswordForm";

export const metadata: Metadata = { title: "Reset your password", robots: { index: false } };

export default function Page() {
  return (
    <FormShell title="Reset your password" intro="Enter your email and we will send you a reset link.">
      <ForgotPasswordForm />
    </FormShell>
  );
}
