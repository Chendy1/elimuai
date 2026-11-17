/** Always rendered so assistive technology announces changes. */
export default function FormFeedback({ error, success }: { error?: string; success?: string }) {
  return (
    <div aria-live="assertive">
      {error ? <p className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-800">{error}</p> : null}
      {success ? <p className="rounded-xl bg-sage px-4 py-3 text-sm text-deep">{success}</p> : null}
    </div>
  );
}
