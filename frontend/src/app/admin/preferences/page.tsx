import { redirect } from "next/navigation";

import { AppHeader } from "@/components/AppHeader";
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
    <div className="flex min-h-full flex-1 flex-col bg-stone-50">
      <AppHeader user={user} />
      <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-5 px-6 py-5">
        <div>
          <h1 className="text-xl font-semibold text-stone-900">本厂偏好</h1>
          <p className="mt-1 text-sm text-stone-500">
            管理员可配常用材料与风险标签展示顺序。报价底稿字段模板在 onboarding 时手工配好，不在这个页面。
          </p>
        </div>
        <CommonMaterialsEditor materials={prefs.common_materials} />
        <RiskLabelPriorityEditor priority={prefs.risk_label_priority} />
        <RiskRuleCatalog items={rules.items} />
      </main>
    </div>
  );
}
