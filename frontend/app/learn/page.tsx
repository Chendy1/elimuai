import type { Metadata } from "next";
import { Suspense } from "react";
import Container from "@/components/Container";
import LearnHome from "@/components/learn/LearnHome";

export const metadata: Metadata = { title: "Learn", robots: { index: false } };

export default function Page() {
  return (
    <Container className="py-12">
      <Suspense fallback={<p className="text-muted">Loading...</p>}>
        <LearnHome />
      </Suspense>
    </Container>
  );
}
