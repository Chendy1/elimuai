import { STATUS_LABEL } from "@/lib/curriculumTree";
import type { ReviewStatus } from "@/lib/types";

const STYLE: Record<ReviewStatus, string> = {
  draft: "bg-sage text-deep",
  in_review: "bg-gold/30 text-deep",
  approved: "bg-forest text-white",
  rejected: "bg-red-100 text-red-800",
};

export default function StatusBadge({ status, testId }: { status: ReviewStatus; testId?: string }) {
  return (
    <span data-testid={testId} className={`rounded-full px-2 py-0.5 text-xs font-semibold ${STYLE[status]}`}>
      {STATUS_LABEL[status]}
    </span>
  );
}
