export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", {
    weekday: "short", day: "numeric", month: "short", year: "numeric",
  });
}

export function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString("en-GB", {
    hour: "2-digit", minute: "2-digit",
  });
}

export function formatTo(fromIso: string, toIso: string): string {
  const from = new Date(fromIso);
  const to = new Date(toIso);
  const time = to.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
  const dayDiff = Math.floor(
    (to.setHours(0, 0, 0, 0) - from.setHours(0, 0, 0, 0)) / 86_400_000
  );
  return dayDiff > 0 ? `${time} +${dayDiff}d` : time;
}

export const KM_TO_NM = 0.539957;

export function formatMonthYear(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", {
    month: "short", year: "numeric",
  });
}

export function formatHours(hours: number): string {
  return `${hours} hr`;
}

export function formatMinutesAsHours(minutes: number): string {
  return `${(minutes / 60).toFixed(2)} hr`;
}
