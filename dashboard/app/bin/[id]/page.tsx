import { PrismaClient } from '@prisma/client';
import Link from 'next/link';

const prisma = new PrismaClient();
export const revalidate = 5;

// Define the expected parameter structure for Next.js 15+
type Props = {
  params: Promise<{ id: string }>;
};

export default async function BinDetails({ params }: Props) {
  // Extract the pi_id from the URL URL
  const { id } = await params;

  // Fetch the specific bin and all its associated image logs from AWS
  const bin = await prisma.device.findUnique({
    where: { pi_id: id },
    include: {
      predictions: {
        orderBy: { timestamp: 'desc' }, // Show newest images first
      },
    },
  });

  // Fallback if someone types a wrong URL
  if (!bin) {
    return (
      <main className="min-h-screen bg-gray-50 p-8 text-center">
        <h1 className="text-2xl font-bold text-red-600 mb-4">Bin Not Found</h1>
        <Link href="/" className="text-blue-600 hover:underline">← Back to Dashboard</Link>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50 p-8 text-gray-900">
      <div className="max-w-6xl mx-auto">
        
        {/* Navigation & Header */}
        <Link href="/" className="inline-block mb-6 text-blue-600 font-semibold hover:underline">
          ← Back to Dashboard
        </Link>
        
        <div className={`p-6 rounded-xl shadow-md border-l-8 mb-8 ${bin.needs_emptying ? 'bg-red-50 border-red-500' : 'bg-white border-green-500'}`}>
          <h1 className="text-3xl font-bold font-mono text-gray-800">{bin.pi_id}</h1>
          <p className="text-lg text-gray-600 mt-1">📍 Location: {bin.location}</p>
          <p className="text-md font-medium mt-2">
            Status: {bin.needs_emptying ? <span className="text-red-600">Needs Emptying</span> : <span className="text-green-600">Operational</span>}
          </p>
        </div>

        {/* --- Specific Bin Logs --- */}
        <section>
          <h2 className="text-2xl font-semibold mb-4">Classification History</h2>
          {bin.predictions.length === 0 ? (
            <p className="text-gray-500 italic">No waste detected by this bin yet.</p>
          ) : (
            <div className="bg-white rounded-xl shadow-md overflow-hidden">
              <table className="w-full text-left">
                <thead className="bg-gray-100 border-b">
                  <tr>
                    <th className="p-4">Image</th>
                    <th className="p-4">Detected Material</th>
                    <th className="p-4">Confidence</th>
                    <th className="p-4">Time</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {bin.predictions.map((log) => (
                    <tr key={log.id} className="hover:bg-gray-50">
                      <td className="p-4">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img src={log.s3_url} alt="Waste" className="h-20 w-20 object-cover rounded-md border" />
                      </td>
                      <td className="p-4 font-semibold capitalize text-lg">{log.waste_class.replace('_', ' ')}</td>
                      <td className="p-4 text-gray-700">{(log.confidence * 100).toFixed(1)}%</td>
                      <td className="p-4 text-sm text-gray-500">{new Date(log.timestamp).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

      </div>
    </main>
  );
}