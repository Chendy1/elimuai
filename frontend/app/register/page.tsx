import type { Metadata } from "next";
import FormShell from "@/components/auth/FormShell";
import RegisterForm from "@/components/auth/RegisterForm";

export const metadata: Metadata = { title: "Create a guardian account", robots: { index: false } };

export default function Page() {
  return (
    <FormShell title="Create a guardian account" intro="A parent or guardian creates the account first. Learner profiles come next.">
      <RegisterForm />
    </FormShell>
  );
}
