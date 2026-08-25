import { redirect } from "next/navigation";

import { AppHeader } from "@/components/AppHeader";
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
    <div className="flex min-h-full flex-1 flex-col bg-stone-50">
      <AppHeader user={user} />
      <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-5 px-6 py-5">
        <div>
          <h1 className="text-xl font-semibold text-stone-900">保密说明</h1>
          <p className="mt-1 text-sm text-stone-500">
            给管理员回答客户安全问卷用。只写当前能核对的事实：图纸存在哪、由谁处理、是否用于训练、DPA
            签了没有。票 02 没关之前，这些格子保持待填。
          </p>
        </div>
        <ConfidentialityNotice notice={notice} />
      </main>
    </div>
  );
}
