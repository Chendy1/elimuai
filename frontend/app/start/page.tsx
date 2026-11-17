import type { Metadata } from "next";
import Button from "@/components/Button";
import Container from "@/components/Container";

export const metadata: Metadata = { title: "Start learning" };

export default function Start() {
  return (
    <Container className="py-16">
      <div className="max-w-2xl rounded-2xl bg-white p-8 shadow-card">
        <h1 className="text-3xl font-bold text-forest">Create a guardian account</h1>
        <p className="mt-3 text-lg text-muted">
          A parent or guardian creates an account first, then adds the learner and gives consent.
          Learner profiles and lessons are still being built, so you can create your account now
          and learning will follow.
        </p>
        <div className="mt-6 flex flex-col gap-3 sm:flex-row">
          <Button href="/register">Create guardian account</Button>
          <Button href="/login" variant="secondary">
            Sign in
          </Button>
        </div>
      </div>
    </Container>
  );
}
