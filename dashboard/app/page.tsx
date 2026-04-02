import { PrismaClient } from '@prisma/client';
import Link from 'next/link';

const prisma = new PrismaClient();

// This forces Next.js to fetch fresh data every 5 seconds
export const revalidate = 5; 

export default async function Dashboard() {
  // Fetch bins and predictions from AWS
  const bins = await prisma.device.findMany();
  const predictions = await prisma.prediction.findMany({
    orderBy: { timestamp: 'desc' },
    take: 10,
    include: { device: true },
  });

  return (
    <main className="min-h-screen bg-gray-50 p-8 text-gray-900">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold mb-8 text-blue-900">Campus Smart Bin Dashboard</h1>

        {/* --- Hardware Status Grid --- */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold mb-4">Live Bin Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {bins.map((bin) => (
              <Link href={`/bin/${bin.pi_id}`} key={bin.pi_id}>
                <div className={`p-6 rounded-xl shadow-md border-l-8 transition-transform cursor-pointer ${bin.needs_emptying ? 'bg-red-50 border-red-500' : 'bg-white border-green-500'}`}>
                  <h3 className="text-lg font-bold font-mono text-gray-700">{bin.pi_id}</h3>
                  <p className="text-gray-500 mb-4">{bin.location}</p>
                  <div className="flex items-center space-x-2">
                    <span className={`h-3 w-3 rounded-full ${bin.needs_emptying ? 'bg-red-500 animate-pulse' : 'bg-green-500'}`}></span>
                    <span className="font-semibold">{bin.needs_emptying ? 'Full - Needs Emptying' : 'Operational'}</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </section>

        {/* --- AI Prediction Logs --- */}
        <section>
          <h2 className="text-2xl font-semibold mb-4">Recent AI Classifications</h2>
          <div className="bg-white rounded-xl shadow-md overflow-hidden">
            <table className="w-full text-left">
              <thead className="bg-gray-100 border-b">
                <tr>
                  <th className="p-4">Image</th>
                  <th className="p-4">Location</th>
                  <th className="p-4">Detected Material</th>
                  <th className="p-4">Confidence</th>
                  <th className="p-4">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {predictions.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="p-4">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img src={log.s3_url} alt="Waste" className="h-16 w-16 object-cover rounded-md border" />
                    </td>
                    <td className="p-4 font-mono text-sm text-gray-600">{log.pi_id}</td>
                    <td className="p-4 font-semibold capitalize">{log.waste_class.replace('_', ' ')}</td>
                    <td className="p-4">{(log.confidence * 100).toFixed(1)}%</td>
                    <td className="p-4 text-sm text-gray-500">{new Date(log.timestamp).toLocaleTimeString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </main>
  );
}