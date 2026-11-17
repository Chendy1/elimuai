import type { Metadata } from "next";
import Container from "@/components/Container";
import SectionHeading from "@/components/SectionHeading";

export const metadata: Metadata = { title: "How it works" };

const STEPS = [
  { title: "Choose your grade", text: "Pick Grade 4 to 9 so everything matches what you are learning." },
  { title: "Find your topic", text: "Move from learning area to strand, sub-strand and topic." },
  { title: "Study the lesson", text: "Read short lessons with examples, activities and a summary." },
  { title: "Ask the tutor", text: "Ask about any part of the lesson and get a step-by-step explanation." },
  { title: "Practise and check progress", text: "Try questions, read the feedback and see what to revise next." },
];

export default function HowItWorks() {
  return (
    <Container className="py-16">
      <SectionHeading
        title="How it works"
        intro="This is the learning journey we are building. It is not available yet."
      />
      <ol className="mt-10 grid max-w-3xl gap-4">
        {STEPS.map((s, i) => (
          <li key={s.title} className="flex gap-4 rounded-2xl bg-white p-5 shadow-card">
            <span
              aria-hidden="true"
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-forest font-bold text-white"
            >
              {i + 1}
            </span>
            <div>
              <h3 className="text-lg font-bold text-forest">{s.title}</h3>
              <p className="text-muted">{s.text}</p>
            </div>
          </li>
        ))}
      </ol>
    </Container>
  );
}
