import type { PendingRevisionsApi } from '~/api/endpoints/pendingRevisions.api'
import type {
  ApprovePendingRevisionRequest,
  ClaimPendingRevisionRequest,
  ListPendingRevisionsQuery,
  RejectPendingRevisionRequest,
  SavePendingRevisionRequest,
} from '~/types/api/requests'
import type { PendingRevision } from '~/types/api/responses'

export class PendingRevisionsService {
  constructor(private readonly api: PendingRevisionsApi) {}

  list(query: ListPendingRevisionsQuery = {}): Promise<PendingRevision[]> {
    return this.api.list(query)
  }

  get(id: string): Promise<PendingRevision> {
    return this.api.get(id)
  }

  claim(ticketId: number, body: ClaimPendingRevisionRequest): Promise<PendingRevision> {
    return this.api.claim(ticketId, body)
  }

  save(id: string, body: SavePendingRevisionRequest): Promise<PendingRevision> {
    return this.api.save(id, body)
  }

  approve(id: string, body: ApprovePendingRevisionRequest = {}) {
    return this.api.approve(id, body)
  }

  reject(id: string, body: RejectPendingRevisionRequest = {}) {
    return this.api.reject(id, body)
  }
}
