import { redirect } from "next/navigation";
import { AppHeader } from "@/components/AppHeader";
import { AppShell } from "@/components/AppShell";
import { ConfidentialityNotice } from "@/components/ConfidentialityNotice";
import { fetchBackend } from "@/lib/backend";
import { parseConfidentialityNotice, parseCurrentUser } from "@/lib/types";

export default async function AdminConfidentialityPage() {
  const [meResponse, noticeResponse] = await Promise.all([
    fetchBackend("/auth/me"),
    fetchBackend("/admin/confidentiality"),
  ]);

  if (meResponse.status === 401 || noticeResponse.status === 401) {
    redirect("/login");
  }
  if (!meResponse.ok) {
    throw new Error("无法读取当前用户");
  }
  const user = parseCurrentUser(await meResponse.json());
  if (user.role !== "admin" || noticeResponse.status === 403) {
    redirect("/part-drawings");
  }
  if (!noticeResponse.ok) {
    throw new Error("无法读取保密说明");
  }
  const notice = parseConfidentialityNotice(await noticeResponse.json());

  return (
    <AppShell user={user}>
      <AppHeader
        title="保密与数据合规说明"
        subtitle="企业安全审计、图纸存储与数据协议（DPA）说明"
      />
      <main className="flex flex-1 flex-col pb-6">
        <div className="glass-card p-5 backdrop-blur-xl">
          <ConfidentialityNotice notice={notice} />
        </div>
      </main>
    </AppShell>
  );
}
