/** Display copy only. Limits are enforced by the backend use-case layer. */
export const MAX_FILE_SIZE_MB = 20;
export const MAX_PDF_PAGES = 20;

export const UPLOAD_ACCEPT =
  ".pdf,.png,.jpg,.jpeg,.webp,.tif,.tiff,application/pdf,image/jpeg,image/png,image/webp,image/tiff";

export function isPdfFile(file: File): boolean {
  return file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
}
