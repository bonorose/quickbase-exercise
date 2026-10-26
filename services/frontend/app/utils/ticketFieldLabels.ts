export const TICKET_FIELD_LABELS: Record<string, string> = {
  title: 'Title',
  contents: 'Contents',
  status: 'Status',
  priority: 'Priority',
}

export function ticketFieldLabel(field: string): string {
  return TICKET_FIELD_LABELS[field] ?? field
}
