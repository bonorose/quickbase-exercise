<script setup lang="ts">
import { AlertTriangle, PanelRightOpen, X } from 'lucide-vue-next'
import type { SidePanelTab } from '~/types/chat'
import { chatReloadTick } from '~/composables/useChat'
import { targetTicketId, ticketRefs } from '~/utils/toolPresenters'

const route = useRoute()
const sessionId = computed(() => {
  const id = route.params.id
  return typeof id === 'string' && id.length > 0 ? id : null
})

const {
  messages,
  status,
  streaming,
  pendingApproval,
  canSend,
  error,
  notFound,
  loadError,
  send,
  stop,
  retryLast,
} = useChat(sessionId)

const approval = useApprovalModal(pendingApproval, streaming)
const { role } = useAuth()

/**
 * The modal keeps its fetched copy of a draft it was asked to set aside. A later turn can add to the
 * same draft and taint it; the stream's copy (`pendingApproval`) has that. Taint only ever turns on.
 */
const draftTainted = computed(() => {
  const held = approval.draft.value
  if (!held) return false
  const streamed = pendingApproval.value
  return held.tainted || (streamed?.id === held.id && streamed.tainted === true)
})
const needsLead = computed(() => draftTainted.value && role.value !== 'team_lead')
const pendingDraftView = computed(() => {
  const held = approval.draft.value
  return held ? { ...held, tainted: draftTainted.value } : pendingApproval.value
})

const showTyping = computed(() => {
  const last = messages.value.at(-1)
  if (!last || last.role !== 'assistant') return true
  return !last.parts.some(part => part.kind === 'text' && part.text.length > 0)
})

const lastModel = computed(() => {
  for (const message of [...messages.value].reverse()) {
    if (message.role === 'assistant' && message.model) return message.model
  }
  return null
})

// ---- Side panel
const panelOpen = ref(true)
const panelExpanded = ref(false)
const panelTab = ref<SidePanelTab>('trace')
const chosenTicketId = ref<number | null>(null)

/** The ticket the panel shows: what the operator picked, else the draft's ticket, else the latest search hit. */
const selectedTicketId = computed<number | null>(() => {
  if (chosenTicketId.value != null) return chosenTicketId.value
  if (approval.draft.value) return approval.draft.value.ticket.id
  for (const message of [...messages.value].reverse()) {
    for (const part of [...message.parts].reverse()) {
      if (part.kind !== 'tool') continue
      const target = targetTicketId(part)
      if (target) return target
      const first = ticketRefs(part.result)[0]
      if (first) return first.id
    }
  }
  return null
})

watch(sessionId, () => {
  chosenTicketId.value = null
})

// Refetch the audit tab after every turn and every decision.
const reloadTick = useState(chatReloadTick, () => 0)
const turnsFinished = ref(0)
watch(streaming, (now, before) => {
  if (before && !now) turnsFinished.value += 1
})
const panelRefreshKey = computed(() => turnsFinished.value + reloadTick.value)

/** "View details" on a proposed change: the open draft opens in the modal, anything else on the Drafts page. */
function review(pendingRevisionId: string) {
  if (approval.draft.value?.id === pendingRevisionId) {
    dismissedWaitingId.value = null
    approval.reopen()
    return
  }
  void navigateTo(`/drafts?id=${pendingRevisionId}`)
}

// ---- Waiting bar (only after "Decide later"); the X hides it until the next draft
const dismissedWaitingId = ref<string | null>(null)
const showWaiting = computed(() =>
  approval.waiting.value && !!approval.draft.value && approval.draft.value.id !== dismissedWaitingId.value,
)
</script>

<template>
  <div class="flex min-h-0 flex-1">
    <SessionList :active-id="sessionId" class="hidden w-72 shrink-0 md:flex" />

    <section class="flex min-h-0 min-w-0 flex-1 flex-col" aria-labelledby="chat-heading">
      <header class="flex items-start justify-between gap-4 border-b bg-background px-6 py-4">
        <div class="flex items-start gap-3">
          <span class="mt-0.5 flex size-9 shrink-0 items-center justify-center rounded-sm border bg-card" aria-hidden="true">
            <BrandMark :wordmark="false" class="scale-[0.7]" />
          </span>
          <div>
            <h1 id="chat-heading" class="text-2xl font-extrabold tracking-tight text-forest">
              Chat
            </h1>
            <p class="text-sm text-muted-foreground">
              Ask about tickets. The assistant can search and draft changes; nothing changes until you approve.
            </p>
          </div>
        </div>
        <div class="flex shrink-0 items-center gap-3 pt-1">
          <NuxtLink
            v-if="sessionId"
            :to="`/audit?session_id=${sessionId}`"
            class="text-sm text-forest underline decoration-teal-signal underline-offset-4 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            data-testid="view-audit"
          >
            View audit
          </NuxtLink>
          <Button
            v-if="!panelOpen"
            type="button"
            variant="outline"
            size="sm"
            class="hidden xl:inline-flex"
            @click="panelOpen = true"
          >
            <PanelRightOpen aria-hidden="true" />
            Tool trace
          </Button>
        </div>
      </header>

      <div v-if="notFound" class="p-6">
        <NotFoundState resource="conversation" to="/chat" link-label="Back to chat" />
      </div>
      <div v-else-if="loadError" class="p-6">
        <Alert variant="destructive">
          <AlertDescription>{{ loadError }}</AlertDescription>
        </Alert>
      </div>
      <template v-else>
        <div v-if="messages.length === 0" class="flex flex-1 items-center justify-center px-6">
          <div class="grid max-w-md justify-items-center gap-3 text-center">
            <BrandMark :wordmark="false" />
            <h2 class="text-lg font-bold text-forest">
              Ask about your team's queue
            </h2>
            <p class="text-sm text-muted-foreground">
              Search tickets, get a summary, or ask the assistant to draft a status or priority change.
              Every change waits for your approval.
            </p>
          </div>
        </div>
        <MessageList
          v-else
          :messages="messages"
          :streaming="streaming"
          :pending-draft="pendingDraftView"
          @review="review"
        >
          <template #after>
            <StreamStatus :status="status" :streaming="streaming" :show-typing="showTyping" class="pl-11" />
          </template>
        </MessageList>

        <div class="border-t bg-background px-6 pb-4 pt-3">
          <div class="mx-auto grid max-w-3xl gap-3">
            <StreamStatus
              v-if="messages.length === 0"
              :status="status"
              :streaming="streaming"
              :show-typing="showTyping"
            />
            <div
              v-if="showWaiting"
              class="flex flex-wrap items-center gap-3 rounded-sm border border-signal/30 bg-signal-wash/60 px-4 py-2.5 text-sm text-forest"
              role="status"
              data-testid="approval-waiting"
            >
              <AlertTriangle class="size-4 shrink-0 text-signal" aria-hidden="true" />
              <span class="flex-1">
                A drafted change to ticket #{{ approval.draft.value!.ticket.id }} is waiting
                {{ needsLead ? 'for a team lead' : 'for your decision' }}.
              </span>
              <Button type="button" size="sm" data-testid="approval-reopen" @click="approval.reopen">
                Review draft
              </Button>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                aria-label="Hide this reminder"
                @click="dismissedWaitingId = approval.draft.value!.id"
              >
                <X aria-hidden="true" />
              </Button>
            </div>
            <Alert v-if="error" variant="destructive">
              <AlertDescription>{{ error }}</AlertDescription>
              <Button
                v-if="messages.some(message => message.role === 'user')"
                type="button"
                variant="outline"
                size="sm"
                class="mt-2"
                @click="retryLast"
              >
                Try again
              </Button>
            </Alert>
            <ChatComposer
              :can-send="canSend"
              :streaming="streaming"
              :show-examples="messages.length === 0"
              :model="lastModel"
              @send="send"
              @stop="stop"
            />
          </div>
        </div>
      </template>
    </section>

    <ChatSidePanel
      v-if="panelOpen"
      v-model:tab="panelTab"
      class="hidden shrink-0 xl:flex"
      :class="panelExpanded ? 'w-[34rem]' : 'w-[23rem]'"
      :messages="messages"
      :session-id="sessionId"
      :selected-ticket-id="selectedTicketId"
      :expanded="panelExpanded"
      :refresh-key="panelRefreshKey"
      @select-ticket="chosenTicketId = $event"
      @review="review"
      @close="panelOpen = false"
      @toggle-expand="panelExpanded = !panelExpanded"
    />

    <ApprovalModal
      :open="approval.open.value"
      :draft="approval.draft.value"
      :can-approve="approval.canApprove.value"
      :needs-lead="approval.needsLead.value"
      @later="approval.decideLater"
      @updated="approval.onUpdated"
      @decided="approval.onDecided"
    />
  </div>
</template>
