interface KpiCardProps {
  title: string;
  value: string;
}

export function KpiCard({ title, value }: KpiCardProps) {
  return (
    <div className="bg-white rounded-2xl p-5 shadow-[0_2px_8px_rgba(0,0,0,0.04)] border border-gray-100 flex flex-col hover:shadow-[0_4px_12px_rgba(0,0,0,0.06)] transition-shadow">
      <div className="flex justify-between items-start mb-2">
        <h3 className="text-gray-500 text-[13px] font-semibold tracking-wide uppercase">{title}</h3>
      </div>
      <div className="flex items-end justify-between mt-1">
        <p className="text-3xl font-bold text-gray-900">{value}</p>
      </div>
    </div>
  );
}
