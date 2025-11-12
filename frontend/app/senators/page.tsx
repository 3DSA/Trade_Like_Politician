import { SenatorsClient } from '@/components/SenatorsClient';

export default function SenatorsPage() {
  return (
    <div className="min-h-screen">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12 md:py-16">
        <div className="mb-12">
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-neutral-900 dark:text-slate-100 mb-4">
            Senator Trading Activity
          </h1>
          <p className="text-lg text-neutral-600 dark:text-slate-400 max-w-3xl leading-relaxed">
            View trading statistics and activity for all senators with disclosed transactions.
          </p>
        </div>

        <div className="space-y-8">
          <SenatorsClient />
        </div>
      </div>
    </div>
  );
}
