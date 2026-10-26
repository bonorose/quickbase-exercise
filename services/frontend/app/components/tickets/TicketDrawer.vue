<script setup lang="ts">
import { formatRelativeTime } from '~/utils/relativeTime'
import { claimConflictOwner, getApiErrorMessage } from '~/utils/apiError'

const props = defineProps<{
  ticketId: number | null
}>()

const emit = defineEmits<{
  close: []
}>()

const { ticket, loading, notFound, errorMessage, refresh } = useTicketDetail(() => props.ticketId)
const open = computed(() => props.ticketId != null)
const claimError = ref<string | null>(null)
const claiming = ref(false)

async function claim(action: 'update' | 'delete') {
  if (props.ticketId == null || claiming.value) return
  claiming.value = true
  claimError.value = null
  try {
    const draft = await useNuxtApp().$services.pendingRevisions.claim(props.ticketId, { action })
    await refresh()
    await navigateTo(`/drafts?id=${draft.id}`)
  }
  catch (error) {
    const owner = claimConflictOwner(error)
    claimError.value = owner
      ? `Being worked on by ${owner.name}`
      : getApiErrorMessage(error, 'Could not start that draft.')
    if (owner) await refresh()
  }
  finally {
    claiming.value = false
  }
}

const dateFormat = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' })
</script>

<template>
  <Sheet :open="open" @update:open="(value) => { if (!value) emit('close') }">
    <SheetContent side="right" class="w-full overflow-y-auto sm:max-w-xl">
      <div v-if="loading" class="grid gap-3">
        <Skeleton class="h-7 w-2/3" />
        <Skeleton class="h-24 w-full" />
        <Skeleton class="h-24 w-full" />
      </div>

      <NotFoundState
        v-else-if="notFound"
        resource="ticket"
        to="/tickets"
        link-label="Back to tickets"
      />

      <Alert v-else-if="errorMessage" variant="destructive">
        <AlertDescription>{{ errorMessage }}</AlertDescription>
      </Alert>

      <template v-else-if="ticket">
        <SheetHeader>
          <SheetTitle class="flex flex-wrap items-center gap-2 text-xl font-extrabold">
            <span class="font-mono text-xs font-medium text-muted-foreground">#{{ ticket.id }}</span>
            {{ ticket.title }}
          </SheetTitle>
          <SheetDescription class="flex flex-wrap gap-2">
            <StatusBadge :status="ticket.status" />
            <PriorityBadge :priority="ticket.priority" />
            <Badge v-if="ticket.openDraft" variant="outline">
              Draft by {{ ticket.openDraft.ownerName }}
            </Badge>
          </SheetDescription>
        </SheetHeader>

        <div class="grid gap-6 text-sm">
          <dl class="grid gap-2 sm:grid-cols-2">
            <div>
              <dt class="text-muted-foreground">
                Submitted by
              </dt>
              <dd>{{ ticket.submittedBy }}</dd>
            </div>
            <div>
              <dt class="text-muted-foreground">
                Last updated by
              </dt>
              <dd>{{ ticket.updatedByName ?? 'Former member' }}</dd>
            </div>
            <div>
              <dt class="text-muted-foreground">
                Created
              </dt>
              <dd class="font-mono text-xs">{{ dateFormat.format(ticket.createdAt) }}</dd>
            </div>
            <div>
              <dt class="text-muted-foreground">
                Updated
              </dt>
              <dd class="font-mono text-xs">{{ formatRelativeTime(ticket.updatedAt) }}</dd>
            </div>
          </dl>

          <section class="grid gap-2">
            <h3 class="font-medium">
              AI summary
            </h3>
            <UntrustedText :text="ticket.description" label="AI summary" :show-label="false" />
          </section>

          <section class="grid gap-2">
            <h3 class="font-medium">
              Contents
            </h3>
            <UntrustedText :text="ticket.contents" label="Ticket contents" :show-label="false" />
          </section>

          <section class="grid gap-2">
            <h3 class="font-medium">
              Revisions
            </h3>
            <RevisionTimeline :revisions="ticket.revisions" />
          </section>

          <section class="grid gap-2">
            <h3 class="font-medium">
              Discussions
            </h3>
            <DiscussionList :discussions="ticket.discussions" />
          </section>

          <p v-if="ticket.openDraft" data-testid="open-draft">
            Being worked on by {{ ticket.openDraft.ownerName }}
          </p>
          <div v-else class="flex flex-wrap gap-2">
            <Button type="button" :disabled="claiming" data-testid="start-working" @click="claim('update')">
              Start working
            </Button>
            <Button type="button" variant="outline" :disabled="claiming" data-testid="request-deletion" @click="claim('delete')">
              Request deletion
            </Button>
          </div>
          <p v-if="claimError" class="text-sm text-signal">
            {{ claimError }}
          </p>
          <NuxtLink v-if="ticket.openDraft" class="text-sm text-forest underline" :to="`/drafts?id=${ticket.openDraft.id}`">
            Open draft
          </NuxtLink>
        </div>
      </template>
    </SheetContent>
  </Sheet>
</template>
