import type { Metadata } from "next";
import { Suspense } from "react";
import Container from "@/components/Container";
import AreaView from "@/components/learn/AreaView";

export const metadata: Metadata = { title: "Subject", robots: { index: false } };

export default async function Page({ params }: { params: Promise<{ areaId: string }> }) {
  const { areaId } = await params;
  return (
    <Container className="py-12">
      <Suspense fallback={<p className="text-muted">Loading...</p>}>
        <AreaView areaId={areaId} />
      </Suspense>
    </Container>
  );
}
