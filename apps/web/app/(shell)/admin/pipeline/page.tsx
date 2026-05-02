import { AdminPipelinePanel } from '@/app/components/AdminPipelinePanel';

export const metadata = {
  title: 'Platform Operations · Downstream Regulatory Intelligence Platform',
  description: 'Trigger ingestion, monitor pipeline runs, and inspect operational health.',
};

export default function PlatformOperationsPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-white">Platform Operations</h1>
      <p className="mt-2 mb-8 max-w-3xl text-slate-400">
        Trigger ingestion, monitor pipeline runs, and inspect operational health. This area is for authorized operators;
        day-to-day consumers use the dashboard and governance views.
      </p>
      <AdminPipelinePanel />
    </div>
  );
}
