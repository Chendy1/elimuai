import ApiStatus from "@/components/ApiStatus";

export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col items-start justify-center gap-6 px-6">
      <span className="rounded-full bg-gold/30 px-3 py-1 text-xs font-semibold text-deep">
        DEMO · foundation build, no learning content yet
      </span>
      <h1 className="text-4xl font-bold text-forest">ElimuAI</h1>
      <p className="text-lg text-muted">
        Curriculum-aligned learning for Kenyan learners. This is the project foundation (Phase 1.1).
      </p>
      <ApiStatus />
    </main>
  );
}
