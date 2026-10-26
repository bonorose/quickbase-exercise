import type { TicketsApi } from '~/api/endpoints/tickets.api'
import type { EditableSnapshot, TicketDetailResponse, TicketSummary } from '~/types/api/responses'
import type { ListTicketsQuery } from '~/types/api/requests'
import type {
  DiscussionView,
  FieldChange,
  OpenDraftView,
  RevisionView,
  TicketDetail,
  TicketRow,
} from '~/types/models'

const SNAPSHOT_FIELDS = ['title', 'contents', 'status', 'priority'] as const

export function unixToDate(seconds: number): Date {
  return new Date(seconds * 1000)
}

export function snapshotDiff(initial: EditableSnapshot, changed: EditableSnapshot): FieldChange[] {
  const changes: FieldChange[] = []
  for (const field of SNAPSHOT_FIELDS) {
    if (initial[field] !== changed[field]) {
      changes.push({ field, from: String(initial[field]), to: String(changed[field]) })
    }
  }
  return changes
}

export function toTicketRow(dto: TicketSummary): TicketRow {
  return {
    id: dto.id,
    status: dto.status,
    priority: dto.priority,
    title: dto.title,
    description: dto.description,
    updatedAt: unixToDate(dto.date_updated),
  }
}

function toRevision(dto: TicketDetailResponse['revisions'][number]): RevisionView {
  return {
    id: dto.id,
    authorName: dto.user.name,
    createdAt: unixToDate(dto.date_created),
    changes: snapshotDiff(dto.initial_contents, dto.changed_contents),
  }
}

function toDiscussion(dto: TicketDetailResponse['discussions'][number]): DiscussionView {
  return {
    id: dto.id,
    authorName: dto.user.name,
    contents: dto.contents,
  }
}

function toOpenDraft(dto: TicketDetailResponse['open_pending_revision']): OpenDraftView | null {
  if (!dto) return null
  return {
    id: dto.id,
    ownerId: dto.owner.id,
    ownerName: dto.owner.name,
    origin: dto.origin,
    tainted: dto.tainted,
    status: dto.status,
    expiresAt: dto.expires_at == null ? null : unixToDate(dto.expires_at),
  }
}

export function toTicketDetail(dto: TicketDetailResponse): TicketDetail {
  return {
    id: dto.id,
    status: dto.status,
    priority: dto.priority,
    title: dto.title,
    description: dto.description,
    contents: dto.contents,
    submittedBy: dto.submitted_by,
    createdAt: unixToDate(dto.date_created),
    updatedByName: dto.updated_by?.name ?? null,
    updatedAt: unixToDate(dto.date_updated),
    revisions: [...dto.revisions]
      .map(toRevision)
      .sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime()),
    discussions: [...dto.discussions]
      .map(toDiscussion)
      .sort((a, b) => a.id - b.id),
    openDraft: toOpenDraft(dto.open_pending_revision),
  }
}

export class TicketsService {
  constructor(private readonly api: TicketsApi) {}

  async list(query: ListTicketsQuery = {}): Promise<{ rows: TicketRow[], total: number, limit: number, offset: number }> {
    const response = await this.api.list(query)
    return {
      rows: response.items.map(toTicketRow),
      total: response.total,
      limit: response.limit,
      offset: response.offset,
    }
  }

  async get(id: number): Promise<TicketDetail> {
    return toTicketDetail(await this.api.get(id))
  }
}
