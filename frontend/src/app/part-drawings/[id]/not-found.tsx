import Link from "next/link";

export default function PartDrawingNotFound() {
  return (
    <main className="flex min-h-full flex-1 flex-col items-center justify-center bg-stone-50 px-6">
      <h1 className="text-lg font-semibold text-stone-900">找不到这张零件图</h1>
      <p className="mt-2 text-sm text-stone-500">它可能不属于本厂，或尚未上传。</p>
      <Link href="/part-drawings" className="mt-6 text-sm text-stone-800 underline">
        返回零件图列表
      </Link>
    </main>
  );
}
