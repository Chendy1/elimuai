import Link from "next/link";
import Container from "./Container";

const LINKS = [
  { href: "/", label: "Home" },
  { href: "/how-it-works", label: "How it works" },
  { href: "/start", label: "Start learning" },
  { href: "/privacy", label: "Privacy" },
  { href: "/terms", label: "Terms" },
];

export default function SiteFooter() {
  return (
    <footer className="mt-24 bg-deep text-white">
      <Container className="py-12">
        <p className="text-xl font-bold">ElimuAI</p>
        <nav aria-label="Footer" className="mt-4 flex flex-wrap gap-x-6 gap-y-2">
          {LINKS.map((l) => (
            <Link key={l.href} href={l.href} className="text-sage underline-offset-4 hover:underline">
              {l.label}
            </Link>
          ))}
        </nav>
        <p className="mt-8 max-w-3xl text-sm text-sage">
          ElimuAI is an independent project under development. It is not endorsed by KICD, the
          Ministry of Education or KNEC. AI-generated content is labelled and is not official
          curriculum material.
        </p>
      </Container>
    </footer>
  );
}
