const GRADES = [4, 5, 6, 7, 8, 9];

export default function GradeSelect({
  id,
  label,
  value,
  onChange,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-semibold text-ink">
        {label}
      </label>
      <select
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 w-full rounded-xl border-2 border-sage bg-white px-4 py-3 text-base text-ink focus:border-forest"
      >
        {GRADES.map((g) => (
          <option key={g} value={String(g)}>
            {"Grade " + g}
          </option>
        ))}
      </select>
    </div>
  );
}
