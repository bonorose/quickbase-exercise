const formatter = new Intl.DateTimeFormat(undefined, { hour: 'numeric', minute: '2-digit' })

/** "10:21 AM" in the viewer's locale. */
export function formatClockTime(date: Date): string {
  return formatter.format(date)
}
