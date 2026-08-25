export function formatDurationSeconds(seconds: number | null): string {
  if (seconds === null) {
    return "—";
  }
  const absolute = Math.abs(seconds);
  if (absolute === 0) {
    return "0 秒";
  }
  if (absolute < 1) {
    return `${seconds.toFixed(2)} 秒`;
  }
  if (absolute < 60) {
    return `${Math.round(seconds)} 秒`;
  }
  const totalSeconds = Math.round(absolute);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const remain = totalSeconds % 60;
  const parts: string[] = [];
  if (hours > 0) {
    parts.push(`${hours} 小时`);
  }
  if (minutes > 0) {
    parts.push(hours > 0 ? `${minutes} 分` : `${minutes} 分钟`);
  }
  if (remain > 0) {
    parts.push(`${remain} 秒`);
  }
  const body = parts.join(" ");
  return seconds < 0 ? `多用 ${body}` : body;
}

export function minutesToSeconds(minutes: number): number {
  return Math.round(minutes * 60);
}
