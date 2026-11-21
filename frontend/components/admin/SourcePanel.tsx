"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { SourcePage } from "@/lib/types";

/** Shows the stored text of a source page so a reviewer can compare it with the draft record. */
export default function SourcePanel({ pageId }: { pageId: string | null }) {
  const [currentId, setCurrentId] = useState<string | null>(pageId);
  const [page, setPage] = useState<SourcePage | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!currentId) return;
    let cancelled = false;
    api<SourcePage>(`/admin/curriculum/source-pages/${currentId}`).then((r) => {
      if (cancelled) return;
      if (r.ok && r.data) {
        setPage(r.data);
        setError("");
      } else setError(r.error ?? "The source page could not be loaded.");
    });
    return () => {
      cancelled = true;
    };
  }, [currentId]);

  if (!pageId) {
    return <p className="rounded-xl bg-gold/20 px-4 py-3 text-sm text-deep">This record has no source page. Check it carefully.</p>;
  }
  if (error) return <p className="text-sm text-red-800">{error}</p>;
  if (!page) return <p className="text-sm text-muted">Loading the source page...</p>;

  return (
    <section aria-label="Source page" className="rounded-xl border-2 border-sage">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b-2 border-sage px-4 py-2 text-sm">
        <p className="text-ink">
          <span className="font-semibold">{page.source_title}</span>
          {" - PDF page " + page.pdf_page + (page.printed_page ? " (printed " + page.printed_page + ")" : "")}
        </p>
        <p className="text-muted">{"Licence: " + page.license_status.replace("_", " ")}</p>
      </div>
      <pre
        data-testid="source-text"
        className="max-h-[28rem] overflow-auto whitespace-pre px-4 py-3 font-mono text-xs leading-5 text-ink"
      >
        {page.text}
      </pre>
      <div className="flex gap-2 border-t-2 border-sage px-4 py-2">
        <button
          type="button"
          disabled={!page.previous_page_id}
          onClick={() => setCurrentId(page.previous_page_id)}
          className="rounded-full border-2 border-forest px-3 py-1 text-sm font-semibold text-forest disabled:opacity-40"
        >
          Previous page
        </button>
        <button
          type="button"
          disabled={!page.next_page_id}
          onClick={() => setCurrentId(page.next_page_id)}
          className="rounded-full border-2 border-forest px-3 py-1 text-sm font-semibold text-forest disabled:opacity-40"
        >
          Next page
        </button>
      </div>
    </section>
  );
}
