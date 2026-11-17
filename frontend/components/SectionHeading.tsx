export default function SectionHeading({
  title,
  intro,
}: {
  title: string;
  intro?: string;
}) {
  return (
    <div className="max-w-2xl">
      <h2 className="text-3xl font-bold text-forest md:text-4xl">{title}</h2>
      {intro ? <p className="mt-3 text-lg text-muted">{intro}</p> : null}
    </div>
  );
}
