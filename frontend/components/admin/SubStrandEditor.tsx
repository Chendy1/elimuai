"use client";

import { useState, type FormEvent } from "react";
import { api } from "@/lib/api";
import { GENERIC_ERROR } from "@/lib/errors";
import {
  formatBlocks, formatCompetencies, formatLines, formatNamed, formatOutcomes, parseBlocks,
  parseCompetencies, parseLines, parseNamed, parseOutcomes,
} from "@/lib/editParse";
import type { SubStrandNode } from "@/lib/types";

const AREA = "w-full rounded-xl border-2 border-sage px-3 py-2 font-mono text-xs leading-5";

function Box({ id, label, hint, value, onChange, rows = 4 }: {
  id: string; label: string; hint?: string; value: string; onChange: (v: string) => void; rows?: number;
}) {
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-semibold text-ink">{label}</label>
      {hint ? <p className="text-xs text-muted">{hint}</p> : null}
      <textarea id={id} rows={rows} value={value} onChange={(e) => onChange(e.target.value)} className={AREA} />
    </div>
  );
}

export default function SubStrandEditor({ sub, csrf, onSaved, onCancel }: {
  sub: SubStrandNode; csrf: string; onSaved: () => void; onCancel: () => void;
}) {
  const [name, setName] = useState(sub.name);
  const [lessons, setLessons] = useState(sub.suggested_lessons === null ? "" : String(sub.suggested_lessons));
  const [topics, setTopics] = useState(formatLines(sub.topics));
  const [outcomes, setOutcomes] = useState(formatOutcomes(sub.outcomes));
  const [experiences, setExperiences] = useState(formatBlocks(sub.experiences));
  const [questions, setQuestions] = useState(formatLines(sub.inquiry_questions));
  const [competencies, setCompetencies] = useState(
    formatCompetencies(sub.competencies.map((c) => ({ code: c.code, description: c.description }))),
  );
  const [values, setValues] = useState(formatNamed(sub.values));
  const [pcis, setPcis] = useState(formatNamed(sub.pcis));
  const [link, setLink] = useState(sub.link_to_other_areas ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function save(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    if (!name.trim()) return setError("The name cannot be empty.");
    const lessonCount = lessons.trim() === "" ? null : Number(lessons);
    if (lessonCount !== null && (!Number.isInteger(lessonCount) || lessonCount < 0 || lessonCount > 500)) {
      return setError("Suggested lessons must be a whole number from 0 to 500.");
    }
    const comp = parseCompetencies(competencies);
    if (comp.unknown.length > 0) {
      return setError("Unknown core competency: " + comp.unknown.join(", ") + ". Use the official names, one per line.");
    }
    setBusy(true);
    const r = await api(`/admin/curriculum/sub-strands/${sub.id}`, {
      method: "PATCH",
      csrf,
      body: {
        name: name.trim(),
        suggested_lessons: lessonCount,
        link_to_other_areas: link.trim() || null,
        topics: parseLines(topics),
        outcomes: parseOutcomes(outcomes),
        experiences: parseBlocks(experiences),
        inquiry_questions: parseLines(questions),
        competencies: comp.items,
        values: parseNamed(values),
        pcis: parseNamed(pcis),
      },
    });
    setBusy(false);
    if (!r.ok) return setError(r.error ?? GENERIC_ERROR);
    onSaved();
  }

  return (
    <form onSubmit={save} className="space-y-4 rounded-xl border-2 border-forest p-4" noValidate aria-label="Edit sub-strand">
      <p className="text-sm text-deep">Saving sends this record back to draft so it must be reviewed again.</p>
      <div>
        <label htmlFor="edit-name" className="block text-sm font-semibold text-ink">Name</label>
        <input id="edit-name" value={name} onChange={(e) => setName(e.target.value)}
          className="w-full rounded-xl border-2 border-sage px-3 py-2 text-sm" />
      </div>
      <div>
        <label htmlFor="edit-lessons" className="block text-sm font-semibold text-ink">Suggested lessons</label>
        <input id="edit-lessons" value={lessons} onChange={(e) => setLessons(e.target.value)} inputMode="numeric"
          className="w-32 rounded-xl border-2 border-sage px-3 py-2 text-sm" />
      </div>
      <Box id="edit-topics" label="Topics" hint="One per line." value={topics} onChange={setTopics} rows={3} />
      <Box id="edit-outcomes" label="Specific learning outcomes" hint="One per line. Start with a) b) c) if the source does."
        value={outcomes} onChange={setOutcomes} rows={6} />
      <Box id="edit-experiences" label="Suggested learning experiences" hint="Separate items with a blank line. Nested points stay inside their item."
        value={experiences} onChange={setExperiences} rows={8} />
      <Box id="edit-questions" label="Key inquiry questions" hint="One per line." value={questions} onChange={setQuestions} rows={3} />
      <Box id="edit-competencies" label="Core competencies" hint="Official name, a colon, then the description. One per line."
        value={competencies} onChange={setCompetencies} rows={3} />
      <Box id="edit-values" label="Values" hint="Name: description. One per line." value={values} onChange={setValues} rows={3} />
      <Box id="edit-pcis" label="Pertinent and contemporary issues"
        hint="Name: description. One per line. Give each one a name." value={pcis} onChange={setPcis} rows={3} />
      <Box id="edit-link" label="Link to other learning areas" value={link} onChange={setLink} rows={2} />
      <div aria-live="assertive">{error ? <p className="text-sm text-red-800">{error}</p> : null}</div>
      <div className="flex gap-2">
        <button type="submit" disabled={busy}
          className="rounded-full bg-forest px-4 py-2 text-sm font-semibold text-white hover:bg-deep disabled:opacity-60">
          Save changes
        </button>
        <button type="button" onClick={onCancel}
          className="rounded-full border-2 border-forest px-4 py-2 text-sm font-semibold text-forest">
          Cancel
        </button>
      </div>
    </form>
  );
}
