/** Turns the plain text boxes of the edit form into the lists the API expects, and back. */

const COMPETENCY_CODES: Record<string, string> = {
  communicationandcollaboration: "communication_collaboration",
  criticalthinkingandproblemsolving: "critical_thinking",
  creativityandimagination: "creativity_imagination",
  citizenship: "citizenship",
  digitalliteracy: "digital_literacy",
  learningtolearn: "learning_to_learn",
  selfefficacy: "self_efficacy",
};
const COMPETENCY_NAMES: Record<string, string> = {
  communication_collaboration: "Communication and Collaboration",
  critical_thinking: "Critical Thinking and Problem Solving",
  creativity_imagination: "Creativity and Imagination",
  citizenship: "Citizenship",
  digital_literacy: "Digital Literacy",
  learning_to_learn: "Learning to Learn",
  self_efficacy: "Self-Efficacy",
};

const squash = (s: string) => s.toLowerCase().replace(/[\s-]+/g, "");

export function parseLines(text: string): string[] {
  return text.split("\n").map((t) => t.trim()).filter(Boolean);
}

/** Items separated by a blank line; line breaks inside an item are kept. */
export function parseBlocks(text: string): string[] {
  return text.split(/\n\s*\n/).map((b) => b.trim()).filter(Boolean);
}

export function parseOutcomes(text: string): { code: string | null; text: string }[] {
  return parseLines(text)
    .map((line) => {
      const m = /^([a-z])\)\s*(.*)$/.exec(line);
      return m ? { code: m[1], text: m[2].trim() } : { code: null, text: line };
    })
    .filter((o) => o.text);
}

export function parseNamed(text: string): { name: string; description: string | null }[] {
  return parseLines(text).map((line) => {
    const i = line.indexOf(":");
    if (i < 1) return { name: line, description: null };
    return { name: line.slice(0, i).trim(), description: line.slice(i + 1).trim() || null };
  });
}

export function parseCompetencies(text: string): {
  items: { code: string; description: string | null }[];
  unknown: string[];
} {
  const items: { code: string; description: string | null }[] = [];
  const unknown: string[] = [];
  for (const { name, description } of parseNamed(text)) {
    const code = COMPETENCY_CODES[squash(name)];
    if (code) items.push({ code, description });
    else unknown.push(name);
  }
  return { items, unknown };
}

export const formatLines = (items: string[]) => items.join("\n");
export const formatBlocks = (items: string[]) => items.join("\n\n");
export const formatOutcomes = (items: { code: string | null; text: string }[]) =>
  items.map((o) => (o.code ? `${o.code}) ${o.text}` : o.text)).join("\n");
export const formatNamed = (items: { name: string; description: string | null }[]) =>
  items.map((i) => (i.description ? `${i.name}: ${i.description}` : i.name)).join("\n");
export const formatCompetencies = (items: { code: string; description: string | null }[]) =>
  items.map((i) => `${COMPETENCY_NAMES[i.code] ?? i.code}${i.description ? `: ${i.description}` : ""}`).join("\n");
