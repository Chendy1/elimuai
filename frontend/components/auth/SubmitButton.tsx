export default function SubmitButton({ busy, children }: { busy: boolean; children: React.ReactNode }) {
  return (
    <button
      type="submit"
      disabled={busy}
      className="w-full rounded-full bg-forest px-6 py-3 text-base font-semibold text-white hover:bg-deep disabled:opacity-60"
    >
      {busy ? "Please wait..." : children}
    </button>
  );
}
