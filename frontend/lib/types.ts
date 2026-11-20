export type User = { id: string; email: string; display_name: string };
export type SessionData = { user: User; csrf_token: string; roles?: string[] };
export type Learner = { id: string; nickname: string; grade: number };
export type ConsentNotice = { version: string; title: string; text: string; is_draft: boolean };

export type ReviewStatus = "draft" | "in_review" | "approved" | "rejected";
export type NamedNote = { name: string; description: string | null };
export type SubStrandNode = {
  id: string; number: string; name: string; suggested_lessons: number | null;
  link_to_other_areas: string | null; topics: string[];
  outcomes: { code: string | null; text: string }[]; experiences: string[]; inquiry_questions: string[];
  competencies: { code: string; name: string; description: string | null }[];
  values: NamedNote[]; pcis: NamedNote[];
  review_status: ReviewStatus; review_comment: string | null; source_page_id: string | null;
};
export type RubricRow = { indicator: string; exceeds: string; meets: string; approaches: string; below: string };
export type StrandNode = {
  id: string; number: string; name: string; unit_id: string | null; rubric: RubricRow[];
  sub_strands: SubStrandNode[];
  review_status: ReviewStatus; review_comment: string | null; source_page_id: string | null;
};
export type AreaNode = {
  id: string; name: string; sort_order: number; archived: boolean; strands: StrandNode[];
  review_status: ReviewStatus; review_comment: string | null; source_page_id: string | null;
};
export type GradeNode = { id: string; level: number; name: string; learning_areas: AreaNode[] };
export type VersionTree = { id: string; label: string; status: "draft" | "published" | "archived"; grades: GradeNode[] };
export type SourcePage = {
  id: string; source_id: string; source_title: string; license_status: string; pdf_page: number;
  printed_page: string | null; text: string; previous_page_id: string | null; next_page_id: string | null;
};
export type CurriculumSummary = { id: string; code: string; name: string; country_code: string };
export type VersionSummary = { id: string; curriculum_id: string; label: string; status: string; published_at: string | null };
