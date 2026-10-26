<script setup lang="ts">
import { AlertTriangle, ChevronDown, Search, SquarePen } from 'lucide-vue-next'
import type { ChatToolPartVM } from '~/services/chat.service'
import type { PendingRevision } from '~/types/api/responses'
import { formatClockTime } from '~/utils/clockTime'
import {
  resultText,
  targetTicketId,
  ticketRefs,
  toolStateLabel,
  toolSummary,
  toolTone,
} from '~/utils/toolPresenters'

const props = defineProps<{
  part: ChatToolPartVM
  time?: Date
  /** The open draft this call raised, when the workspace knows it (adds the tainted warning). */
  draft?: PendingRevision | null
}>()

const emit = defineEmits<{ review: [pendingRevisionId: string] }>()

const SHOWN_TICKETS = 3

const open = ref(false)
const showAll = ref(false)
const tickets = computed(() => ticketRefs(props.part.result))
const visibleTickets = computed(() => (showAll.value ? tickets.value : tickets.value.slice(0, SHOWN_TICKETS)))
const stateLabel = computed(() => toolStateLabel(props.part))
const tone = computed(() => toolTone(props.part))
const summary = computed(() => toolSummary(props.part))
const failed = computed(() => props.part.ok === false)
const isSearch = computed(() => props.part.name === 'search_tickets')
const targetId = computed(() => targetTicketId(props.part))
const attention = computed(() => tone.value === 'attention' && !!props.part.pending_revision_id)
const tainted = computed(() => !!props.draft && props.draft.id === props.part.pending_revision_id && props.draft.tainted)
const proposed = computed(() => {
  const fields = props.part.args.fields
  if (!fields || typeof fields !== 'object') return []
  return Object.entries(fields as Record<string, unknown>)
    .filter(([, value]) => value != null)
    .map(([field, value]) => `${field} → ${String(value)}`)
})
const body = computed(() => (failed.value ? props.part.error ?? '' : resultText(props.part.result)))

const pillClass: Record<ReturnType<typeof toolTone>, string> = {
  running: 'bg-muted text-ink',
  done: 'bg-teal-wash text-forest',
  attention: 'bg-signal-wash text-signal',
  failed: 'border border-signal text-signal',
  closed: 'bg-muted text-ink',
}
</script>

<template>
  <div
    class="rounded-sm border bg-card"
    :class="attention ? 'border-signal/40' : ''"
    data-testid="tool-trace"
  >
    <button
      type="button"
      class="flex w-full items-center gap-2 px-3 pt-2.5 text-left text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
      :class="open ? 'pb-2' : 'pb-1'"
      :aria-expanded="open"
      @click="open = !open"
    >
      <Search v-if="isSearch" class="size-4 shrink-0 text-forest" aria-hidden="true" />
      <SquarePen v-else class="size-4 shrink-0" :class="attention ? 'text-signal' : 'text-forest'" aria-hidden="true" />
      <span class="font-mono text-[13px] text-forest">{{ part.name }}</span>
      <span
        class="rounded-full px-2 py-0.5 text-[11px] font-semibold"
        :class="pillClass[tone]"
        data-testid="tool-state"
      >{{ stateLabel }}</span>
      <time v-if="time" class="ml-auto font-mono text-[11px] text-muted-foreground" :datetime="time.toISOString()">
        {{ formatClockTime(time) }}
      </time>
      <ChevronDown
        class="size-4 shrink-0 text-muted-foreground transition-transform"
        :class="[open ? 'rotate-180' : '', time ? '' : 'ml-auto']"
        aria-hidden="true"
      />
    </button>
    <p class="px-3 text-xs text-muted-foreground" :class="attention ? 'sr-only' : 'pb-2.5'">
      {{ summary }}
    </p>
    <div v-if="attention" class="h-2" aria-hidden="true" />

    <div
      v-if="attention"
      class="mx-3 mb-3 grid gap-1.5 rounded-sm border border-signal/30 bg-signal-wash/60 px-3 py-2.5 text-sm"
      data-testid="tool-pending"
    >
      <p class="flex items-center gap-2 font-medium text-forest">
        <AlertTriangle class="size-4 shrink-0 text-signal" aria-hidden="true" />
        <span>
          {{ part.args.action === 'delete' ? 'Proposed deletion of ticket' : 'Proposed change to ticket' }}
          <NuxtLink v-if="targetId" :to="`/tickets?id=${targetId}`" class="underline underline-offset-2">#{{ targetId }}</NuxtLink>
        </span>
      </p>
      <p v-if="proposed.length" class="pl-6 font-mono text-xs text-forest">
        {{ proposed.join(' · ') }}
      </p>
      <p class="pl-6 text-xs text-ink">
        <template v-if="tainted">
          It was drafted after reading ticket text, so a team lead must approve it.
        </template>
        <template v-else>
          Nothing changes until it's approved.
        </template>
      </p>
      <div class="flex justify-end">
        <button
          type="button"
          class="text-xs font-medium text-forest underline decoration-teal-signal underline-offset-4 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          data-testid="tool-review"
          @click="emit('review', part.pending_revision_id as string)"
        >
          View details
        </button>
      </div>
    </div>

    <div v-if="open" class="grid gap-3 border-t px-3 py-3">
      <div>
        <p class="text-[11px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
          Requested arguments
        </p>
        <pre class="mt-1 overflow-x-auto rounded-sm bg-muted px-3 py-2 font-mono text-xs">{{ JSON.stringify(part.args, null, 2) }}</pre>
      </div>

      <div v-if="isSearch && !failed && part.ok === true" class="grid gap-1.5">
        <p class="text-[11px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
          Result
        </p>
        <p class="font-mono text-xs text-forest">
          Found {{ tickets.length }} {{ tickets.length === 1 ? 'ticket' : 'tickets' }}
        </p>
        <ul v-if="tickets.length" class="grid gap-1 text-sm">
          <li v-for="ticket in visibleTickets" :key="ticket.id" class="flex gap-2">
            <span class="font-mono text-xs leading-5 text-muted-foreground">#{{ ticket.id }}</span>
            <NuxtLink class="text-forest underline decoration-teal-signal underline-offset-4" :to="`/tickets?id=${ticket.id}`">
              {{ ticket.title }}
            </NuxtLink>
          </li>
        </ul>
        <button
          v-if="tickets.length > SHOWN_TICKETS && !showAll"
          type="button"
          class="justify-self-start font-mono text-xs text-forest underline underline-offset-4"
          @click="showAll = true"
        >
          +{{ tickets.length - SHOWN_TICKETS }} more
        </button>
      </div>
      <UntrustedText
        v-else-if="body"
        :text="body"
        :label="failed ? 'Error' : 'Result'"
        :class="failed ? 'text-signal' : ''"
      />

      <NuxtLink
        v-if="part.pending_revision_id"
        class="text-sm text-forest underline decoration-teal-signal underline-offset-4"
        :to="`/drafts?id=${part.pending_revision_id}`"
        data-testid="draft-link"
      >
        Open draft
      </NuxtLink>
    </div>
  </div>
</template>
