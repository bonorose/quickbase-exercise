<script setup lang="ts">
import type { AuditEvent } from '~/types/api/responses'
import { getApiErrorMessage, isNotFound } from '~/utils/apiError'
import { unixToDate } from '~/services/tickets.service'

useHead({ title: 'Audit' })

const PAGE_SIZE = 20

const route = useRoute()
const { role } = useAuth()
const { audit } = useServices()
const items = ref<AuditEvent[]>([])
const total = ref(0)
const ticketId = ref(typeof route.query.ticket_id === 'string' ? route.query.ticket_id : '')
const expandedId = ref<number | null>(null)
const loading = ref(true)
const loadingMore = ref(false)
const notFound = ref(false)
const errorMessage = ref<string | null>(null)
const dateFormat = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' })

const sessionId = computed(() => typeof route.query.session_id === 'string' ? route.query.session_id : '')
const hasMore = computed(() => items.value.length < total.value)

function actorLabel(item: AuditEvent) {
  if (item.actor?.name) return item.actor.name
  if (item.actor_type === 'agent') return 'qAI assistant'
  if (item.actor_type === 'system') return 'System'
  return item.actor_type
}

function payloadText(payload: Record<string, unknown>) {
  return JSON.stringify(payload, null, 2)
}

async function load(append = false) {
  if (append) loadingMore.value = true
  else {
    loading.value = true
    expandedId.value = null
  }
  notFound.value = false
  errorMessage.value = null
  const parsed = Number(ticketId.value)
  const ticketFilter = role.value === 'team_lead' && Number.isInteger(parsed) && parsed > 0 ? parsed : undefined
  try {
    const page = await audit.list({
      limit: PAGE_SIZE,
      offset: append ? items.value.length : 0,
      ticket_id: ticketFilter,
      session_id: sessionId.value || undefined,
    })
    items.value = append ? [...items.value, ...page.items] : page.items
    total.value = page.total
  }
  catch (error) {
    if (!append && isNotFound(error)) {
      notFound.value = true
      items.value = []
      total.value = 0
    }
    else if (!append) {
      errorMessage.value = getApiErrorMessage(error, 'Could not load the audit log.')
      items.value = []
      total.value = 0
    }
    else {
      errorMessage.value = getApiErrorMessage(error, 'Could not load more events.')
    }
  }
  finally {
    loading.value = false
    loadingMore.value = false
  }
}

function togglePayload(id: number) {
  expandedId.value = expandedId.value === id ? null : id
}

onMounted(() => load())
watch(sessionId, () => load())
</script>

<template>
  <div class="grid gap-6">
    <div>
      <h1 class="text-3xl font-extrabold tracking-tight text-forest">
        Audit
      </h1>
      <p class="text-muted-foreground">
        {{ role === 'team_lead' ? 'Your organization.' : 'Your activity.' }}
      </p>
    </div>

    <p v-if="sessionId" class="text-sm text-muted-foreground">
      This conversation only.
      <NuxtLink to="/audit" class="text-forest underline">
        Show all
      </NuxtLink>
    </p>

    <form v-if="role === 'team_lead'" class="flex items-end gap-2" @submit.prevent="load(false)">
      <label class="grid gap-1 text-sm">
        Ticket
        <Input v-model="ticketId" inputmode="numeric" data-testid="audit-ticket-filter" />
      </label>
      <Button type="submit" variant="outline">
        Filter
      </Button>
    </form>

    <NotFoundState v-if="notFound" resource="ticket" to="/audit" link-label="Back to the audit log" />
    <Alert v-else-if="errorMessage" variant="destructive">
      <AlertDescription>{{ errorMessage }}</AlertDescription>
    </Alert>
    <p v-else-if="loading" class="text-sm text-muted-foreground">
      Loading the audit log…
    </p>
    <p v-else-if="items.length === 0" class="text-sm text-muted-foreground">
      No audit events yet.
    </p>
    <Table v-else>
      <TableHeader>
        <TableRow>
          <TableHead>When</TableHead>
          <TableHead>Event</TableHead>
          <TableHead>Actor</TableHead>
          <TableHead>Ticket</TableHead>
          <TableHead>Session</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <template v-for="item in items" :key="item.id">
          <TableRow>
            <TableCell class="font-mono text-xs">
              {{ dateFormat.format(unixToDate(item.date_created)) }}
            </TableCell>
            <TableCell>
              <button
                type="button"
                class="text-left underline-offset-2 hover:underline focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                :aria-expanded="expandedId === item.id"
                @click="togglePayload(item.id)"
              >
                {{ item.event }}
              </button>
            </TableCell>
            <TableCell>{{ actorLabel(item) }}</TableCell>
            <TableCell>{{ item.ticket_id ?? '—' }}</TableCell>
            <TableCell>
              <NuxtLink
                v-if="item.session_id"
                :to="`/audit?session_id=${item.session_id}`"
                class="text-forest underline"
              >
                Session
              </NuxtLink>
              <span v-else>—</span>
            </TableCell>
          </TableRow>
          <TableRow v-if="expandedId === item.id">
            <TableCell colspan="5">
              <UntrustedText :text="payloadText(item.payload)" label="Payload" />
            </TableCell>
          </TableRow>
        </template>
      </TableBody>
    </Table>
    <div v-if="!loading" class="flex items-center gap-3">
      <p class="text-xs text-muted-foreground">
        {{ total }} events
      </p>
      <Button
        v-if="hasMore"
        type="button"
        variant="outline"
        size="sm"
        :disabled="loadingMore"
        data-testid="audit-load-more"
        @click="load(true)"
      >
        {{ loadingMore ? 'Loading…' : 'Load more' }}
      </Button>
    </div>
  </div>
</template>
