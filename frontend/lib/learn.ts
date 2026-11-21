export type LearnArea = { id: string; name: string };
export type LearnSubStrand = {
  id: string; number: string; name: string; suggested_lessons: number | null;
  topics: string[]; outcomes: { code: string | null; text: string }[]; inquiry_questions: string[];
};
export type LearnTree = {
  id: string; name: string;
  strands: { id: string; number: string; name: string; sub_strands: LearnSubStrand[] }[];
  sources: { title: string; publisher: string }[];
  version: { id: string; label: string; status: string };
};

/** Builds "?a=1&b=2", skipping empty values. */
export function queryString(params: Record<string, string | null | undefined>): string {
  const parts = Object.entries(params)
    .filter(([, v]) => v !== null && v !== undefined && v !== "")
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`);
  return parts.length ? `?${parts.join("&")}` : "";
}

/** Staff can preview any version by passing its id; learners never pass one. */
export function previewQuery(version: string | null): string {
  return queryString({ version_id: version });
}

export function learnHref(path: string, ctx: { version?: string | null; learner?: string | null; grade?: string | null; sub?: string | null }): string {
  return path + queryString({ version: ctx.version, learner: ctx.learner, grade: ctx.grade, sub: ctx.sub });
}

export function attribution(sources: { title: string; publisher: string }[]): string[] {
  return sources.map((s) => `${s.publisher}, ${s.title}`);
}
