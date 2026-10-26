<script setup lang="ts">
import {
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Clock,
  ExternalLink,
  Loader2,
  Maximize2,
  Minimize2,
  X,
  XCircle,
} from 'lucide-vue-next'
import type { ChatMessageVM, ChatToolPartVM } from '~/services/chat.service'
import type { SidePanelTab } from '~/types/chat'
import { formatClockTime } from '~/utils/clockTime'
import { formatRelativeTime } from '~/utils/relativeTime'
import {
  isReadOnlyTool,
  targetTicketId,
  ticketRefs,
  toolStateLabel,
  toolSummary,
  toolTone,
} from '~/utils/toolPresenters'

const props = defineProps<{
  messages: ChatMessageVM[]
  sessionId: string | null
  selectedTicketId: number | null
  expanded: boolean
  /** Bumped after each turn and decision so the audit tab refetches. */
  refreshKey: number
}>()

const tab = defineModel<SidePanelTab>('tab', { default: 'trace' })

const emit = defineEmits<{
  selectTicket: [id: number]
  review: [pendingRevisionId: string]
  close: []
  toggleExpand: []
}>()

const TABS: { id: SidePanelTab, label: string }[] = [
  { id: 'trace', label: 'Tool Trace' },
  { id: 'ticket', label: 'Ticket Details' },
  { id: 'audit', label: 'Audit' },
]

// ---- Tool trace: every call in the conversation, in order
interface TraceEntry { part: ChatToolPartVM, time: Date }
const entries = computed<TraceEntry[]>(() =>
  props.messages.flatMap(message =>
    message.role !== 'assistant'
      ? []
      : message.parts.flatMap(part => (part.kind === 'tool' ? [{ part, time: message.createdAt }] : [])),
  ),
)
const openEntries = ref(new Set<string>())
function toggleEntry(callId: string) {
  const next = new Set(openEntries.value)
  if (next.has(callId)) next.delete(callId)
  else next.add(callId)
  openEntries.value = next
}

function showTicket(id: number) {
  emit('selectTicket', id)
  tab.value = 'ticket'
}

// ---- Ticket details
const { ticket, loading: ticketLoading, notFound: ticketNotFound, errorMessage: ticketError } = useTicketDetail(
  () => props.selectedTicketId,
)

// ---- Audit (this conversation)
const { audit } = useServices()
const { data: auditPage, status: auditStatus } = useAsyncData(
  () => `chat:audit:${props.sessionId ?? 'none'}:${props.refreshKey}`,
  async () => (props.sessionId ? audit.list({ session_id: props.sessionId, limit: 25 }) : null),
  { watch: [() => props.sessionId, () => props.refreshKey] },
)
const auditEvents = computed(() => auditPage.value?.items ?? [])

// ---- Tabs keyboard support (arrow keys move between tabs)
function onTabKey(event: KeyboardEvent, index: number) {
  if (event.key !== 'ArrowRight' && event.key !== 'ArrowLeft') return
  event.preventDefault()
  const next = (index + (event.key === 'ArrowRight' ? 1 : TABS.length - 1)) % TABS.length
  tab.value = TABS[next]!.id
  nextTick(() => document.getElementById(`side-tab-${TABS[next]!.id}`)?.focus())
}

const iconTone: Record<ReturnType<typeof toolTone>, string> = {
  running: 'text-ink',
  done: 'text-teal-signal',
  attention: 'text-signal',
  failed: 'text-signal',
  closed: 'text-ink',
}
</script>

<template>
  <aside class="flex min-h-0 flex-col border-l bg-card" aria-label="Conversation details" data-testid="chat-side-panel">
    <div class="flex items-center gap-1 border-b px-3">
      <div role="tablist" aria-label="Details" class="flex flex-1 gap-1">
        <button
          v-for="(item, index) in TABS"
          :id="`side-tab-${item.id}`"
          :key="item.id"
          type="button"
          role="tab"
          :aria-selected="tab === item.id"
          :aria-controls="`side-panel-${item.id}`"
          :tabindex="tab === item.id ? 0 : -1"
          class="-mb-px border-b-2 px-2.5 py-3 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          :class="tab === item.id ? 'border-forest font-semibold text-forest' : 'border-transparent text-muted-foreground hover:text-forest'"
          @click="tab = item.id"
          @keydown="onTabKey($event, index)"
        >
          {{ item.label }}
        </button>
      </div>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        :aria-label="expanded ? 'Narrow the panel' : 'Widen the panel'"
        @click="emit('toggleExpand')"
      >
        <Minimize2 v-if="expanded" aria-hidden="true" />
        <Maximize2 v-else aria-hidden="true" />
      </Button>
      <Button type="button" variant="ghost" size="icon" aria-label="Hide the panel" @click="emit('close')">
        <X aria-hidden="true" />
      </Button>
    </div>

    <!-- Tool Trace -->
    <div
      v-if="tab === 'trace'"
      id="side-panel-trace"
      role="tabpanel"
      aria-labelledby="side-tab-trace"
      class="min-h-0 flex-1 overflow-y-auto p-4"
    >
      <p v-if="entries.length === 0" class="text-sm text-muted-foreground">
        Tool calls show up here as the assistant works - what it called, with which arguments, and what came back.
      </p>
      <ol v-else class="grid">
        <li
          v-for="(entry, index) in entries"
          :key="entry.part.call_id"
          class="relative grid grid-cols-[1.5rem_minmax(0,1fr)] gap-x-3 pb-5"
          data-testid="panel-trace-item"
        >
          <span
            v-if="index < entries.length - 1"
            class="absolute left-[0.7rem] top-6 bottom-0 w-px bg-rule"
            aria-hidden="true"
          />
          <span class="relative mt-0.5" :class="iconTone[toolTone(entry.part)]" aria-hidden="true">
            <CheckCircle2 v-if="toolTone(entry.part) === 'done'" class="size-5" />
            <Clock v-else-if="toolTone(entry.part) === 'attention'" class="size-5" />
            <XCircle v-else-if="toolTone(entry.part) === 'failed' || toolTone(entry.part) === 'closed'" class="size-5" />
            <Loader2 v-else class="size-5 animate-spin motion-reduce:animate-none" />
          </span>
          <div class="grid min-w-0 gap-1">
            <div class="flex flex-wrap items-center gap-2">
              <span class="font-mono text-[13px] font-medium text-forest">{{ entry.part.name }}</span>
              <span
                v-if="isReadOnlyTool(entry.part.name)"
                class="rounded-full bg-teal-wash px-2 py-0.5 text-[11px] font-semibold text-forest"
              >Read only</span>
              <span
                v-if="!isReadOnlyTool(entry.part.name) || toolTone(entry.part) !== 'done'"
                class="rounded-full px-2 py-0.5 text-[11px] font-semibold"
                :class="toolTone(entry.part) === 'attention' ? 'bg-signal-wash text-signal' : 'bg-muted text-ink'"
              >{{ toolStateLabel(entry.part) }}</span>
              <time class="ml-auto font-mono text-[11px] text-muted-foreground" :datetime="entry.time.toISOString()">
                {{ formatClockTime(entry.time) }}
              </time>
            </div>
            <p class="text-xs text-ink">
              {{ toolSummary(entry.part) }}
            </p>

            <button
              type="button"
              class="flex items-center gap-1 justify-self-start text-xs font-medium text-forest focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              :aria-expanded="openEntries.has(entry.part.call_id)"
              @click="toggleEntry(entry.part.call_id)"
            >
              <ChevronDown
                class="size-3.5 transition-transform"
                :class="openEntries.has(entry.part.call_id) ? '' : '-rotate-90'"
                aria-hidden="true"
              />
              Arguments
            </button>
            <pre
              v-if="openEntries.has(entry.part.call_id)"
              class="overflow-x-auto rounded-sm bg-muted px-3 py-2 font-mono text-xs"
            >{{ JSON.stringify(entry.part.args, null, 2) }}</pre>

            <div v-if="entry.part.ok === false && entry.part.error" class="text-xs text-signal">
              <UntrustedText :text="entry.part.error" label="Error" :lines="3" />
            </div>
            <div
              v-else-if="isReadOnlyTool(entry.part.name) && entry.part.ok === true"
              class="flex items-center justify-between gap-2 text-xs"
            >
              <span class="text-ink">{{ ticketRefs(entry.part.result).length }} tickets found</span>
              <button
                v-if="ticketRefs(entry.part.result).length"
                type="button"
                class="flex items-center gap-0.5 font-medium text-forest underline decoration-teal-signal underline-offset-4"
                @click="showTicket(ticketRefs(entry.part.result)[0]!.id)"
              >
                View results
                <ChevronRight class="size-3.5" aria-hidden="true" />
              </button>
            </div>
            <div v-else-if="entry.part.pending_revision_id" class="flex items-center justify-end gap-3 text-xs">
              <button
                v-if="targetTicketId(entry.part)"
                type="button"
                class="font-medium text-forest underline underline-offset-4"
                @click="showTicket(targetTicketId(entry.part)!)"
              >
                Ticket #{{ targetTicketId(entry.part) }}
              </button>
              <button
                type="button"
                class="font-medium text-forest underline decoration-teal-signal underline-offset-4"
                @click="emit('review', entry.part.pending_revision_id!)"
              >
                View details
              </button>
            </div>
          </div>
        </li>
      </ol>
    </div>

    <!-- Ticket Details -->
    <div
      v-else-if="tab === 'ticket'"
      id="side-panel-ticket"
      role="tabpanel"
      aria-labelledby="side-tab-ticket"
      class="min-h-0 flex-1 overflow-y-auto p-4"
    >
      <p v-if="selectedTicketId == null" class="text-sm text-muted-foreground">
        Pick a ticket from a search result or a proposed change to see its details here.
      </p>
      <p v-else-if="ticketLoading" class="text-sm text-muted-foreground">
        Loading ticket…
      </p>
      <NotFoundState v-else-if="ticketNotFound" resource="ticket" to="/tickets" link-label="Go to tickets" />
      <Alert v-else-if="ticketError" variant="destructive">
        <AlertDescription>{{ ticketError }}</AlertDescription>
      </Alert>
      <div v-else-if="ticket" class="grid gap-4" data-testid="panel-ticket">
        <div class="flex items-start gap-2">
          <p class="font-mono text-lg font-semibold text-forest">
            #{{ ticket.id }}
          </p>
          <h3 class="flex-1 pt-1 text-sm font-semibold text-forest">
            {{ ticket.title }}
          </h3>
          <NuxtLink
            :to="`/tickets?id=${ticket.id}`"
            class="pt-1 text-muted-foreground hover:text-forest"
            aria-label="Open in Tickets"
          >
            <ExternalLink class="size-4" aria-hidden="true" />
          </NuxtLink>
        </div>
        <dl class="grid grid-cols-[7rem_minmax(0,1fr)] gap-x-3 gap-y-2.5 text-sm">
          <dt class="text-muted-foreground">
            Status
          </dt>
          <dd><StatusBadge :status="ticket.status" /></dd>
          <dt class="text-muted-foreground">
            Priority
          </dt>
          <dd><PriorityBadge :priority="ticket.priority" /></dd>
          <dt class="text-muted-foreground">
            Submitted by
          </dt>
          <dd class="truncate">
            {{ ticket.submittedBy }}
          </dd>
          <dt class="text-muted-foreground">
            Created
          </dt>
          <dd>{{ ticket.createdAt.toLocaleDateString() }}</dd>
          <dt class="text-muted-foreground">
            Updated
          </dt>
          <dd>{{ formatRelativeTime(ticket.updatedAt) }}<template v-if="ticket.updatedByName"> · {{ ticket.updatedByName }}</template></dd>
        </dl>
        <div v-if="ticket.openDraft" class="rounded-sm border border-signal/30 bg-signal-wash/60 px-3 py-2 text-xs text-forest">
          Being worked on by {{ ticket.openDraft.ownerName }}<template v-if="ticket.openDraft.tainted"> · needs a team lead</template>
        </div>
        <div class="grid gap-1.5">
          <h4 class="text-sm font-semibold text-forest">
            Summary
          </h4>
          <UntrustedText :text="ticket.description" label="AI summary of the ticket" :lines="5" />
        </div>
        <p class="text-xs text-muted-foreground">
          {{ ticket.revisions.length }} {{ ticket.revisions.length === 1 ? 'revision' : 'revisions' }} ·
          {{ ticket.discussions.length }} {{ ticket.discussions.length === 1 ? 'discussion' : 'discussions' }}
        </p>
      </div>
    </div>

    <!-- Audit -->
    <div
      v-else
      id="side-panel-audit"
      role="tabpanel"
      aria-labelledby="side-tab-audit"
      class="min-h-0 flex-1 overflow-y-auto p-4"
    >
      <p v-if="!sessionId" class="text-sm text-muted-foreground">
        The audit trail of this conversation shows up once it has started.
      </p>
      <p v-else-if="auditStatus === 'pending' && auditEvents.length === 0" class="text-sm text-muted-foreground">
        Loading audit…
      </p>
      <p v-else-if="auditEvents.length === 0" class="text-sm text-muted-foreground">
        No audit events for this conversation yet.
      </p>
      <ol v-else class="grid gap-3">
        <li v-for="event in auditEvents" :key="event.id" class="grid gap-0.5 border-b pb-3 text-sm last:border-b-0">
          <div class="flex items-center gap-2">
            <span class="font-mono text-[13px] text-forest">{{ event.event }}</span>
            <time class="ml-auto font-mono text-[11px] text-muted-foreground" :datetime="new Date(event.date_created * 1000).toISOString()">
              {{ formatClockTime(new Date(event.date_created * 1000)) }}
            </time>
          </div>
          <p class="text-xs text-ink">
            {{ event.actor?.name ?? event.actor_type }}<template v-if="event.ticket_id"> · ticket #{{ event.ticket_id }}</template>
          </p>
        </li>
      </ol>
      <NuxtLink
        v-if="sessionId"
        :to="`/audit?session_id=${sessionId}`"
        class="mt-4 inline-block text-sm text-forest underline decoration-teal-signal underline-offset-4"
      >
        Open the full audit trail
      </NuxtLink>
    </div>
  </aside>
</template>
