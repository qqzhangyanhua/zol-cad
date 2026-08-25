import { redirect } from "next/navigation";

import { AppHeader } from "@/components/AppHeader";
import { CorrectionStatsPanel } from "@/components/CorrectionStatsPanel";
import { fetchBackend } from "@/lib/backend";
import { parseCorrectionStats, parseCurrentUser } from "@/lib/types";

export default async function CorrectionStatsPage() {
  const [meResponse, statsResponse] = await Promise.all([
    fetchBackend("/auth/me"),
    fetchBackend("/correction-stats"),
  ]);

  if (meResponse.status === 401 || statsResponse.status === 401) {
    redirect("/login");
  }
  if (!meResponse.ok) {
    throw new Error("无法读取当前用户");
  }
  const user = parseCurrentUser(await meResponse.json());
  if (user.role !== "admin" || statsResponse.status === 403) {
    redirect("/part-drawings");
  }
  if (!statsResponse.ok) {
    throw new Error("无法读取修正记录统计");
  }
  const stats = parseCorrectionStats(await statsResponse.json());

  return (
    <div className="flex min-h-full flex-1 flex-col bg-stone-50">
      <AppHeader user={user} />
      <main className="px-6 py-5">
        <CorrectionStatsPanel stats={stats} />
      </main>
    </div>
  );
}
