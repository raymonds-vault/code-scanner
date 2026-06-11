const colours: Record<string, string> = {
  high: "bg-red-100 text-red-700 ring-1 ring-red-200",
  medium: "bg-orange-100 text-orange-700 ring-1 ring-orange-200",
  low: "bg-yellow-100 text-yellow-700 ring-1 ring-yellow-200",
};

export default function SeverityBadge({ severity }: { severity: string }) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium capitalize ${
        colours[severity.toLowerCase()] ?? "bg-neutral-100 text-neutral-600"
      }`}
    >
      {severity}
    </span>
  );
}
