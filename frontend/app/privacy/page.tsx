import type { Metadata } from "next";
import Container from "@/components/Container";

export const metadata: Metadata = { title: "Privacy" };

export default function Page() {
  return (
    <Container className="py-16">
      <div className="max-w-3xl">
        <p className="inline-block rounded-full bg-gold/30 px-3 py-1 text-xs font-semibold text-deep">
          Draft placeholder
        </p>
        <h1 className="mt-4 text-3xl font-bold text-forest">Privacy</h1>
        <p className="mt-4 text-lg text-muted">
          This page is a placeholder. The final text will be written after legal review and a Data
          Protection Impact Assessment, and before any learner can register. Nothing here is a
          binding policy yet.
        </p>
      </div>
    </Container>
  );
}
