'use client';

import { useParams } from 'next/navigation';
import { SenatorProfileClient } from '@/components/SenatorProfileClient';

export default function SenatorPage() {
  const params = useParams();
  const senatorName = decodeURIComponent(params.name as string);

  return (
    <div className="min-h-screen">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12 md:py-16">
        <div className="mb-12">
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-neutral-900 dark:text-slate-100 mb-4">
            {senatorName}
          </h1>
          <p className="text-lg text-neutral-600 dark:text-slate-400">Trading activity and statistics</p>
        </div>

        <div className="space-y-8">
          <SenatorProfileClient senatorName={senatorName} />
        </div>
      </div>
    </div>
  );
}
