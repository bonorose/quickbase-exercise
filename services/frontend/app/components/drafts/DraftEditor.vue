<script setup lang="ts">
import type { PendingRevision, TicketPriority, TicketStatus } from '~/types/api/responses'
import type { ChangedContentsRequest } from '~/types/api/requests'
import { messageForDraftFailure, statusOf } from '~/utils/apiError'
import { draftRemainingMs } from '~/utils/draftExpiry'
import { ticketFieldLabel } from '~/utils/ticketFieldLabels'

const props = defineProps<{
  draft: PendingRevision
  canApprove?: boolean
}>()

const emit = defineEmits<{
  updated: [draft: PendingRevision]
  decided: [draft: PendingRevision]
}>()

const STATUSES: TicketStatus[] = ['open', 'blocked', 'closed']
const PRIORITIES: TicketPriority[] = ['lowest', 'low', 'medium', 'high', 'critical']
const WARN_MS = 120_000

const action = ref<'update' | 'delete'>(props.draft.action)
const title = ref(props.draft.changed_contents.title ?? '')
const contents = ref(props.draft.changed_contents.contents ?? '')
const status = ref<TicketStatus | ''>(props.draft.changed_contents.status ?? '')
const priority = ref<TicketPriority | ''>(props.draft.changed_contents.priority ?? '')
const reason = ref('')
const errorMessage = ref<string | null>(null)
const expired = ref(props.draft.status === 'expired')
const forbidden = ref(false)
const busy = ref(false)
const nowMs = ref(Date.now())
const receivedAtMs = ref(Date.now())
let timer: ReturnType<typeof setInterval> | undefined

watch(() => props.draft, (draft) => {
  receivedAtMs.value = Date.now()
  action.value = draft.action
  title.value = draft.changed_contents.title ?? ''
  contents.value = draft.changed_contents.contents ?? ''
  status.value = draft.changed_contents.status ?? ''
  priority.value = draft.changed_contents.priority ?? ''
  expired.value = draft.status === 'expired'
  forbidden.value = false
  errorMessage.value = null
})

onMounted(() => {
  timer = setInterval(() => {
    nowMs.value = Date.now()
  }, 1000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})

const remainingMs = computed(() => draftRemainingMs(props.draft, receivedAtMs.value, nowMs.value))

const expiryLabel = computed(() => {
  if (remainingMs.value == null) return null
  if (remainingMs.value <= 0) return 'This draft has expired'
  const total = Math.ceil(remainingMs.value / 1000)
  const minutes = Math.floor(total / 60)
  const seconds = total % 60
  return `Expires in ${minutes}:${String(seconds).padStart(2, '0')}`
})

const expiryUrgent = computed(() => remainingMs.value != null && remainingMs.value <= WARN_MS)
const timedOut = computed(() => expired.value || (remainingMs.value != null && remainingMs.value <= 0))
const allowEdit = computed(() => props.draft.status === 'open' && !timedOut.value)
const allowApprove = computed(() => props.canApprove !== false && allowEdit.value && !forbidden.value)

function changedContents(): ChangedContentsRequest {
  const changed: ChangedContentsRequest = {}
  const nextTitle = title.value.trim()
  if (nextTitle) changed.title = nextTitle
  if (contents.value) changed.contents = contents.value
  if (status.value) changed.status = status.value
  if (priority.value) changed.priority = priority.value
  return changed
}

async function run(task: () => Promise<void>) {
  if (busy.value) return
  busy.value = true
  errorMessage.value = null
  try {
    await task()
  }
  catch (error) {
    const status = statusOf(error)
    errorMessage.value = messageForDraftFailure(error)
    if (status === 410) expired.value = true
    if (status === 403) forbidden.value = true
    if (status === 409) {
      try {
        emit('updated', await useServices().pendingRevisions.get(props.draft.id))
      }
      catch {
        // Keep the stale-rebase copy even if reload fails.
      }
    }
  }
  finally {
    busy.value = false
  }
}

function save() {
  return run(async () => {
    const draft = await useServices().pendingRevisions.save(props.draft.id, {
      action: action.value,
      changed_contents: changedContents(),
    })
    emit('updated', draft)
  })
}

function approve() {
  return run(async () => {
    const result = await useServices().pendingRevisions.approve(props.draft.id, {
      action: action.value,
      changed_contents: changedContents(),
    })
    emit('decided', result.pending_revision)
  })
}

function reject() {
  return run(async () => {
    const draft = await useServices().pendingRevisions.reject(props.draft.id, {
      reason: reason.value.trim() || undefined,
    })
    emit('decided', draft)
  })
}
</script>

<template>
  <div class="grid gap-4" data-testid="draft-editor">
    <Alert v-if="draft.tainted">
      <AlertDescription>
        This draft was written after the assistant read ticket text. A team lead has to approve it.
      </AlertDescription>
    </Alert>

    <p
      v-if="expiryLabel"
      class="text-sm"
      :class="expiryUrgent ? 'font-medium text-signal' : 'text-muted-foreground'"
      data-testid="draft-expiry"
    >
      {{ expiryLabel }}
    </p>

    <dl v-if="Object.keys(draft.diff).length" class="grid gap-1 text-sm">
      <div v-for="(change, field) in draft.diff" :key="field" class="flex flex-wrap gap-2">
        <dt class="font-medium">{{ ticketFieldLabel(String(field)) }}</dt>
        <dd class="text-muted-foreground">{{ change.from }} → {{ change.to }}</dd>
      </div>
    </dl>

    <label class="grid gap-1 text-sm">
      Action
      <select v-model="action" class="h-9 rounded-sm border border-input bg-card px-2" data-testid="draft-action">
        <option value="update">Update</option>
        <option value="delete">Delete</option>
      </select>
    </label>
    <label class="grid gap-1 text-sm">
      Title
      <Input v-model="title" data-testid="draft-title" />
    </label>
    <label class="grid gap-1 text-sm">
      Contents
      <textarea
        v-model="contents"
        rows="4"
        data-testid="draft-contents"
        class="rounded-sm border border-input bg-card px-3 py-2 text-sm"
      />
    </label>
    <div class="grid gap-3 sm:grid-cols-2">
      <label class="grid gap-1 text-sm">
        Status
        <select v-model="status" class="h-9 rounded-sm border border-input bg-card px-2" data-testid="draft-status">
          <option value="">Keep current</option>
          <option v-for="item in STATUSES" :key="item" :value="item">{{ item }}</option>
        </select>
      </label>
      <label class="grid gap-1 text-sm">
        Priority
        <select v-model="priority" class="h-9 rounded-sm border border-input bg-card px-2" data-testid="draft-priority">
          <option value="">Keep current</option>
          <option v-for="item in PRIORITIES" :key="item" :value="item">{{ item }}</option>
        </select>
      </label>
    </div>
    <label class="grid gap-1 text-sm">
      Reject reason
      <Input v-model="reason" data-testid="draft-reason" />
    </label>

    <Alert v-if="errorMessage" variant="destructive">
      <AlertDescription>{{ errorMessage }}</AlertDescription>
    </Alert>

    <div class="flex flex-wrap gap-2">
      <Button type="button" variant="outline" :disabled="busy || !allowEdit" data-testid="draft-save" @click="save">
        Save
      </Button>
      <Button v-if="allowApprove" type="button" :disabled="busy" data-testid="draft-approve" @click="approve">
        Approve
      </Button>
      <Button type="button" variant="outline" :disabled="busy || !allowEdit" data-testid="draft-reject" @click="reject">
        Reject
      </Button>
    </div>
  </div>
</template>
