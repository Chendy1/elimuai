import type { Metadata } from "next";
import VersionReview from "@/components/admin/VersionReview";
import Container from "@/components/Container";

export const metadata: Metadata = { title: "Review curriculum version", robots: { index: false } };

export default async function Page({ params }: { params: Promise<{ versionId: string }> }) {
  const { versionId } = await params;
  return (
    <Container className="py-12">
      <VersionReview versionId={versionId} />
    </Container>
  );
}
