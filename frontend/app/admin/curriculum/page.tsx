import type { Metadata } from "next";
import CurriculumList from "@/components/admin/CurriculumList";
import Container from "@/components/Container";

export const metadata: Metadata = { title: "Curriculum review", robots: { index: false } };

export default function Page() {
  return (
    <Container className="py-12">
      <CurriculumList />
    </Container>
  );
}
