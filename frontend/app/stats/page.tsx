import { StatsClient } from '@/components/StatsClient';

export default function StatsPage() {
  return (
    <div className="min-h-screen">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12 md:py-16">
        <div className="mb-12">
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-neutral-900 dark:text-slate-100 mb-4">
            Overall Statistics
          </h1>
          <p className="text-lg text-neutral-600 dark:text-slate-400 max-w-3xl leading-relaxed">
            Aggregate data from all U.S. Senate financial disclosures and trading activity.
          </p>
        </div>

        <div className="space-y-8">
          <StatsClient />
        </div>
      </div>
    </div>
  );
}
