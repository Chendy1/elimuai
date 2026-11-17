import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ElimuAI",
  description: "Curriculum-aligned learning for Kenyan learners. Under development.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
