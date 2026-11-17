import type { Metadata } from "next";
import Button from "@/components/Button";
import Container from "@/components/Container";

export const metadata: Metadata = { title: "Start learning" };

export default function Start() {
  return (
    <Container className="py-16">
      <div className="max-w-2xl rounded-2xl bg-white p-8 shadow-card">
        <h1 className="text-3xl font-bold text-forest">Registration is not open yet</h1>
        <p className="mt-3 text-lg text-muted">
          ElimuAI is still being built. When it opens, a parent or guardian will create the
          learner profile and give consent, or a school will create accounts for its learners.
        </p>
        <Button href="/how-it-works" variant="secondary" className="mt-6">
          See how it will work
        </Button>
      </div>
    </Container>
  );
}
