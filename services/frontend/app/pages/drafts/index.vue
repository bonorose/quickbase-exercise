<script setup lang="ts">
import type { PendingRevision } from '~/types/api/responses'
import { chatReloadTick } from '~/composables/useChat'
import { getApiErrorMessage } from '~/utils/apiError'

useHead({ title: 'Drafts' })

const route = useRoute()
const { pendingRevisions } = useServices()
const { role } = useAuth()
const drafts = ref<PendingRevision[]>([])
const selected = ref<PendingRevision | null>(null)
const loading = ref(true)
const errorMessage = ref<string | null>(null)

const canApprove = computed(() => {
  if (!selected.value?.tainted) return true
  return role.value === 'team_lead'
})

async function load() {
  loading.value = true
  errorMessage.value = null
  try {
    drafts.value = await pendingRevisions.list({ scope: 'mine', status: 'open' })
    const id = typeof route.query.id === 'string' ? route.query.id : ''
    if (!id) {
      selected.value = null
      return
    }
    selected.value = drafts.value.find(item => item.id === id) ?? await pendingRevisions.get(id)
  }
  catch (error) {
    selected.value = null
    errorMessage.value = getApiErrorMessage(error, 'Could not load drafts.')
  }
  finally {
    loading.value = false
  }
}

function openDraft(draft: PendingRevision) {
  void navigateTo({ path: '/drafts', query: { id: draft.id } })
}

function closeDraft() {
  selected.value = null
  void navigateTo('/drafts')
}

function onUpdated(draft: PendingRevision) {
  selected.value = draft
  void load()
}

function onDecided() {
  useState(chatReloadTick, () => 0).value += 1
  closeDraft()
  void load()
}

onMounted(load)
watch(() => route.query.id, load)
</script>

<template>
  <div class="grid gap-6">
    <div>
      <h1 class="text-3xl font-extrabold tracking-tight text-forest">
        Drafts
      </h1>
      <p class="text-muted-foreground">
        Your open pending revisions.
      </p>
    </div>

    <Alert v-if="errorMessage" variant="destructive">
      <AlertDescription>{{ errorMessage }}</AlertDescription>
    </Alert>
    <p v-else-if="loading" class="text-sm text-muted-foreground">
      Loading drafts…
    </p>
    <p v-else-if="drafts.length === 0" class="text-sm text-muted-foreground">
      You have no open drafts.
    </p>
    <ul v-else class="grid gap-2">
      <li v-for="draft in drafts" :key="draft.id">
        <button
          type="button"
          class="w-full rounded-sm border bg-card px-3 py-2 text-left text-sm"
          :data-testid="`draft-row-${draft.ticket.id}`"
          :data-ticket-id="String(draft.ticket.id)"
          :data-draft-id="draft.id"
          @click="openDraft(draft)"
        >
          <span class="font-medium">{{ draft.ticket.title }}</span>
          <span class="ml-2 text-muted-foreground">{{ draft.action }}</span>
          <span v-if="draft.tainted" class="ml-2 text-signal">Needs a team lead</span>
        </button>
      </li>
    </ul>

    <ReviewDialog
      :open="selected != null"
      :draft="selected"
      :can-approve="canApprove"
      @close="closeDraft"
      @updated="onUpdated"
      @decided="onDecided"
    />
  </div>
</template>
