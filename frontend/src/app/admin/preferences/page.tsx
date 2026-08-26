import { redirect } from "next/navigation";
import { AppHeader } from "@/components/AppHeader";
import { AppShell } from "@/components/AppShell";
import { CommonMaterialsEditor } from "@/components/CommonMaterialsEditor";
import { RiskLabelPriorityEditor } from "@/components/RiskLabelPriorityEditor";
import { RiskRuleCatalog } from "@/components/RiskRuleCatalog";
import { fetchBackend } from "@/lib/backend";
import { parseCurrentUser, parseFactoryPreferences, parseRiskRuleList } from "@/lib/types";

export default async function AdminPreferencesPage() {
  const [meResponse, prefsResponse, rulesResponse] = await Promise.all([
    fetchBackend("/auth/me"),
    fetchBackend("/factory-preferences"),
    fetchBackend("/admin/risk-rules"),
  ]);

  if (meResponse.status === 401 || prefsResponse.status === 401 || rulesResponse.status === 401) {
    redirect("/login");
  }
  if (!meResponse.ok) {
    throw new Error("无法读取当前用户");
  }
  const user = parseCurrentUser(await meResponse.json());
  if (user.role !== "admin" || rulesResponse.status === 403) {
    redirect("/part-drawings");
  }
  if (!prefsResponse.ok || !rulesResponse.ok) {
    throw new Error("无法读取本厂偏好");
  }
  const prefs = parseFactoryPreferences(await prefsResponse.json());
  const rules = parseRiskRuleList(await rulesResponse.json());

  return (
    <AppShell user={user}>
      <AppHeader
        title="本厂偏好与风险规则"
        subtitle="配置常用材料清单与制造风险规则优先级排序"
      />
      <main className="flex flex-1 flex-col gap-5 pb-6">
        <div className="glass-card p-5 backdrop-blur-xl">
          <CommonMaterialsEditor materials={prefs.common_materials} />
        </div>
        <div className="glass-card p-5 backdrop-blur-xl">
          <RiskLabelPriorityEditor priority={prefs.risk_label_priority} />
        </div>
        <div className="glass-card p-5 backdrop-blur-xl">
          <RiskRuleCatalog items={rules.items} />
        </div>
      </main>
    </AppShell>
  );
}
