import Link from "next/link";

type Props = {
  href: string;
  variant?: "primary" | "secondary";
  className?: string;
  children: React.ReactNode;
};

const base =
  "inline-flex items-center justify-center rounded-full px-6 py-3 text-base font-semibold transition-colors";
const variants = {
  primary: "bg-forest text-white hover:bg-deep",
  secondary: "border-2 border-forest text-forest hover:bg-sage",
};

export default function Button({ href, variant = "primary", className = "", children }: Props) {
  return (
    <Link href={href} className={`${base} ${variants[variant]} ${className}`}>
      {children}
    </Link>
  );
}
