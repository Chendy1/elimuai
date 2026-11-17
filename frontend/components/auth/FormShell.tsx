import Container from "@/components/Container";

export default function FormShell({
  title,
  intro,
  children,
}: {
  title: string;
  intro?: string;
  children: React.ReactNode;
}) {
  return (
    <Container className="py-12">
      <div className="mx-auto max-w-md rounded-2xl bg-white p-8 shadow-card">
        <h1 className="text-3xl font-bold text-forest">{title}</h1>
        {intro ? <p className="mt-2 text-muted">{intro}</p> : null}
        <div className="mt-6">{children}</div>
      </div>
    </Container>
  );
}
