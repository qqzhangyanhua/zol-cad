import { redirect } from "next/navigation";

import { AppHeader } from "@/components/AppHeader";
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
    <div className="flex min-h-full flex-1 flex-col bg-stone-50">
      <AppHeader user={user} />
      <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-6 px-6 py-6">
        <div>
          <h1 className="text-xl font-semibold text-stone-900">报价任务</h1>
          <p className="mt-1 text-sm text-stone-500">
            轻量归集层：把一次询价里的多张零件图归到一起。产品核心仍是单张图的提取与复核。
          </p>
        </div>
        <QuoteTaskCreateForm />
        <QuoteTaskSearchForm values={filters} />
        {list.items.length === 0 ? (
          filters.customer_name || filters.created_from || filters.created_to || filters.review_status ? (
            <p className="rounded-xl border border-dashed border-stone-200 bg-white px-4 py-10 text-center text-sm text-stone-500">
              没有符合检索条件的报价任务。
            </p>
          ) : (
            <EmptyQuoteTaskState />
          )
        ) : (
          <QuoteTaskList items={list.items} />
        )}
      </main>
    </div>
  );
}
