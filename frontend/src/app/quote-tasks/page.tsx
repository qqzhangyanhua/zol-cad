import { redirect } from "next/navigation";
import { AppHeader } from "@/components/AppHeader";
import { AppShell } from "@/components/AppShell";
import { EmptyQuoteTaskState } from "@/components/EmptyQuoteTaskState";
import { QuoteTaskCreateForm } from "@/components/QuoteTaskCreateForm";
import { QuoteTaskList } from "@/components/QuoteTaskList";
import { QuoteTaskSearchForm } from "@/components/QuoteTaskSearchForm";
import { fetchBackend } from "@/lib/backend";
import {
  parseCurrentUser,
  parseQuoteTaskList,
  quoteTaskSearchQuery,
  type QuoteTaskReviewStatus,
  type QuoteTaskSearchParams,
} from "@/lib/types";

type QuoteTasksPageProps = {
  searchParams: Promise<{
    customer_name?: string;
    created_from?: string;
    created_to?: string;
    review_status?: string;
  }>;
};

function asSearchParams(raw: {
  customer_name?: string;
  created_from?: string;
  created_to?: string;
  review_status?: string;
}): QuoteTaskSearchParams {
  const reviewStatus = raw.review_status;
  const allowed: readonly string[] = ["无零件图", "复核未完成", "已复核"];
  return {
    customer_name: raw.customer_name,
    created_from: raw.created_from,
    created_to: raw.created_to,
    review_status:
      reviewStatus && allowed.includes(reviewStatus)
        ? (reviewStatus as QuoteTaskReviewStatus)
        : "",
  };
}

export default async function QuoteTasksPage({ searchParams }: QuoteTasksPageProps) {
  const raw = await searchParams;
  const filters = asSearchParams(raw);
  const [meResponse, listResponse] = await Promise.all([
    fetchBackend("/auth/me"),
    fetchBackend(`/quote-tasks${quoteTaskSearchQuery(filters)}`),
  ]);

  if (meResponse.status === 401 || listResponse.status === 401) {
    redirect("/login");
  }
  if (!meResponse.ok || !listResponse.ok) {
    throw new Error("无法读取报价任务");
  }

  const user = parseCurrentUser(await meResponse.json());
  const list = parseQuoteTaskList(await listResponse.json());

  return (
    <AppShell user={user}>
      <AppHeader
        title="报价任务管理"
        subtitle={
          user.role === "admin"
            ? "全厂报价任务归集与多图纸进度管理"
            : "自己处理过的报价任务归集"
        }
      />
      <main className="flex flex-1 flex-col gap-4 pb-6">
        <QuoteTaskCreateForm />
        <QuoteTaskSearchForm values={filters} />
        {list.items.length === 0 ? (
          filters.customer_name || filters.created_from || filters.created_to || filters.review_status ? (
            <div className="glass-card p-10 text-center text-xs text-slate-500">
              没有符合检索条件的报价任务。
            </div>
          ) : (
            <EmptyQuoteTaskState />
          )
        ) : (
          <QuoteTaskList items={list.items} />
        )}
      </main>
    </AppShell>
  );
}
