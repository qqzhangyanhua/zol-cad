import { redirect } from "next/navigation";
import { AppHeader } from "@/components/AppHeader";
import { AppShell } from "@/components/AppShell";
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
    <AppShell user={user}>
      <AppHeader
        title="字段修正统计与复核洞察"
        subtitle="统计人工修正频率较高的特征字段，辅助算法持续微调"
      />
      <main className="flex flex-1 flex-col pb-6">
        <div className="glass-card p-5 backdrop-blur-xl">
          <CorrectionStatsPanel stats={stats} />
        </div>
      </main>
    </AppShell>
  );
}
