import type { Metadata } from "next";
import Container from "@/components/Container";
import LearnersPanel from "@/components/learners/LearnersPanel";

export const metadata: Metadata = { title: "Your learners", robots: { index: false } };

export default function Page() {
  return (
    <Container className="py-12">
      <div className="mx-auto max-w-2xl">
        <LearnersPanel />
      </div>
    </Container>
  );
}
