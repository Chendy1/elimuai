import type { Metadata } from "next";
import AccountPanel from "@/components/auth/AccountPanel";
import Container from "@/components/Container";

export const metadata: Metadata = { title: "Your account", robots: { index: false } };

export default function Page() {
  return (
    <Container className="py-12">
      <div className="mx-auto max-w-xl rounded-2xl bg-white p-8 shadow-card">
        <AccountPanel />
      </div>
    </Container>
  );
}
