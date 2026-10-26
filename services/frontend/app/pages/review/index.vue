<script setup lang="ts">
import type { PendingRevision } from '~/types/api/responses'
import { chatReloadTick } from '~/composables/useChat'
import { getApiErrorMessage } from '~/utils/apiError'

useHead({ title: 'Review' })

const { role } = useAuth()
const { pendingRevisions } = useServices()
const ready = computed(() => role.value != null)
const allowed = computed(() => role.value === 'team_lead')
const drafts = ref<PendingRevision[]>([])
const selected = ref<PendingRevision | null>(null)
const loading = ref(false)
const errorMessage = ref<string | null>(null)

async function load() {
  if (!allowed.value) return
  loading.value = true
  errorMessage.value = null
  try {
    drafts.value = await pendingRevisions.list({ scope: 'lead_queue' })
  }
  catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Could not load the review queue.')
  }
  finally {
    loading.value = false
  }
}

function onDecided() {
  useState(chatReloadTick, () => 0).value += 1
  selected.value = null
  void load()
}

watch(allowed, () => {
  void load()
}, { immediate: true })
</script>

<template>
  <NotFoundState
    v-if="ready && !allowed"
    resource="page"
    to="/"
    link-label="Back to the dashboard"
  />
  <div v-else-if="allowed" class="grid gap-6">
    <div>
      <h1 class="text-3xl font-extrabold tracking-tight text-forest">
        Review
      </h1>
      <p class="text-muted-foreground">
        Open drafts that need a team lead.
      </p>
    </div>
    <Alert v-if="errorMessage" variant="destructive">
      <AlertDescription>{{ errorMessage }}</AlertDescription>
    </Alert>
    <p v-else-if="loading" class="text-sm text-muted-foreground">
      Loading the queue…
    </p>
    <p v-else-if="drafts.length === 0" class="text-sm text-muted-foreground">
      Nothing is waiting for review.
    </p>
    <ul v-else class="grid gap-2">
      <li v-for="draft in drafts" :key="draft.id">
        <button
          type="button"
          class="w-full rounded-sm border bg-card px-3 py-2 text-left text-sm"
          :data-testid="`review-row-${draft.ticket.id}`"
          :data-ticket-id="String(draft.ticket.id)"
          @click="selected = draft"
        >
          <span class="font-medium">{{ draft.ticket.title }}</span>
          <span class="ml-2 text-muted-foreground">by {{ draft.owner.name }}</span>
        </button>
      </li>
    </ul>
    <ReviewDialog
      :open="selected != null"
      :draft="selected"
      :can-approve="true"
      @close="selected = null"
      @updated="selected = $event"
      @decided="onDecided"
    />
  </div>
</template>
