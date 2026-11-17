"use client";

import Link from "next/link";
import { useState } from "react";
import Button from "./Button";
import Container from "./Container";

const LINKS = [
  { href: "/", label: "Home" },
  { href: "/how-it-works", label: "How it works" },
  { href: "/login", label: "Sign in" },
];

export default function SiteHeader() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 border-b border-sage bg-ivory/95 backdrop-blur">
      <Container className="flex h-16 items-center justify-between">
        <Link href="/" className="text-xl font-bold text-forest">
          ElimuAI
        </Link>

        <nav aria-label="Main" className="hidden items-center gap-6 md:flex">
          {LINKS.map((l) => (
            <Link key={l.href} href={l.href} className="font-medium text-ink hover:text-forest">
              {l.label}
            </Link>
          ))}
          <Button href="/start" className="!py-2">
            Start learning
          </Button>
        </nav>

        <button
          type="button"
          className="rounded-full border-2 border-forest px-4 py-2 text-sm font-semibold text-forest md:hidden"
          aria-expanded={open}
          aria-controls="mobile-menu"
          onClick={() => setOpen((o) => !o)}
        >
          {open ? "Close menu" : "Open menu"}
        </button>
      </Container>

      {open ? (
        <nav id="mobile-menu" aria-label="Mobile" className="border-t border-sage bg-white md:hidden">
          <Container className="flex flex-col gap-1 py-3">
            {LINKS.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                onClick={() => setOpen(false)}
                className="rounded-lg px-2 py-3 text-lg font-medium text-ink hover:bg-sage"
              >
                {l.label}
              </Link>
            ))}
            <Button href="/start" className="mt-2">
              Start learning
            </Button>
          </Container>
        </nav>
      ) : null}
    </header>
  );
}
