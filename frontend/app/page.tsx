import Button from "@/components/Button";
import Container from "@/components/Container";
import SectionHeading from "@/components/SectionHeading";

const GRADES = [4, 5, 6, 7, 8, 9];

const PLANNED = [
  {
    title: "AI tutor",
    text: "A patient tutor that knows your grade and topic, explains step by step, gives Kenyan examples and asks questions to check understanding.",
  },
  {
    title: "Voice learning",
    text: "Ask questions and listen to explanations in English and Kiswahili. Voice will always be optional, with a text alternative.",
  },
  {
    title: "Practice and assessment",
    text: "Practice questions with clear feedback and explanations. ElimuAI practice is not an official KNEC exam or grade.",
  },
  {
    title: "Personalised progress",
    text: "See what you have practised, what is going well and what to revise next.",
  },
  {
    title: "Parents and teachers",
    text: "Guardians give consent and follow progress. Teachers can set activities and see where a class needs help.",
  },
  {
    title: "Institutional partners",
    text: "Learning stays free for learners. Schools, foundations and organisations will be able to support access, with aggregate reporting only.",
  },
];

const FAQ = [
  {
    q: "Is ElimuAI free?",
    a: "The goal is for learning to be completely free for learners, funded by partners and not by advertising or by selling data.",
  },
  {
    q: "Is ElimuAI official curriculum material?",
    a: "No. ElimuAI is an independent project. It is not endorsed by KICD, the Ministry of Education or KNEC. Every lesson will be labelled by where it came from.",
  },
  {
    q: "Can I use it today?",
    a: "Not yet. This site is under development and learner registration is not open.",
  },
];

export default function Home() {
  return (
    <>
      <section className="bg-gradient-to-b from-sage/60 to-ivory">
        <Container className="py-16 md:py-24">
          <span className="rounded-full bg-gold/30 px-3 py-1 text-xs font-semibold text-deep">
            In development
          </span>
          <h1 className="mt-5 max-w-3xl text-4xl font-extrabold leading-tight text-forest md:text-6xl">
            A smarter way to learn. Built for Kenya.
          </h1>
          <p className="mt-5 max-w-2xl text-lg text-muted md:text-xl">
            Personalised, curriculum-aligned learning and an AI tutor that helps every learner
            understand more, practise confidently and reach their potential.
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Button href="/start">{"Start Learning — It's Free"}</Button>
            <Button href="/how-it-works" variant="secondary">
              Explore How It Works
            </Button>
          </div>
        </Container>
      </section>

      <section className="py-16">
        <Container>
          <SectionHeading
            title="Grades 4 to 9"
            intro="Designed around Kenya's Competency-Based Education curriculum. Content will be added only from verified sources and reviewed before it reaches learners."
          />
          <ul className="mt-8 flex flex-wrap gap-3">
            {GRADES.map((g) => (
              <li
                key={g}
                className="rounded-2xl bg-white px-6 py-4 text-lg font-semibold text-forest shadow-card"
              >
                Grade {g}
              </li>
            ))}
          </ul>
        </Container>
      </section>

      <section className="py-8">
        <Container>
          <SectionHeading
            title="What we are building"
            intro="These features are planned and are not available yet."
          />
          <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {PLANNED.map((p) => (
              <article key={p.title} className="rounded-2xl bg-white p-6 shadow-card">
                <h3 className="text-xl font-bold text-forest">{p.title}</h3>
                <p className="mt-2 text-muted">{p.text}</p>
              </article>
            ))}
          </div>
        </Container>
      </section>

      <section className="py-16" aria-labelledby="faq-title">
        <Container>
          <h2 id="faq-title" className="text-3xl font-bold text-forest md:text-4xl">
            Frequently asked questions
          </h2>
          <div className="mt-6 max-w-3xl divide-y divide-sage rounded-2xl bg-white shadow-card">
            {FAQ.map((f) => (
              <details key={f.q} className="group p-5">
                <summary className="cursor-pointer text-lg font-semibold text-ink">{f.q}</summary>
                <p className="mt-2 text-muted">{f.a}</p>
              </details>
            ))}
          </div>
        </Container>
      </section>
    </>
  );
}
