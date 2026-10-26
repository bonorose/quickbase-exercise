<script setup lang="ts">
import { ChevronDown, Plus } from 'lucide-vue-next'
import { formatRelativeTime } from '~/utils/relativeTime'

defineProps<{ activeId: string | null }>()

const { sessions, hasMore, loadingMore, pending, loadMore } = useChatSessions()
</script>

<template>
  <aside class="flex min-h-0 flex-col border-r bg-card" data-testid="session-list" aria-label="Conversations">
    <div class="flex items-center justify-between gap-2 px-4 py-4">
      <h2 class="text-base font-bold text-forest">
        Conversations
      </h2>
      <Button as-child size="sm">
        <NuxtLink to="/chat">
          <Plus aria-hidden="true" />
          New chat
        </NuxtLink>
      </Button>
    </div>
    <div class="min-h-0 flex-1 overflow-y-auto px-2 pb-2">
      <p v-if="pending && sessions.length === 0" class="px-2 text-sm text-muted-foreground">
        Loading conversations…
      </p>
      <p v-else-if="sessions.length === 0" class="px-2 text-sm text-muted-foreground">
        No conversations yet.
      </p>
      <ul v-else class="grid gap-0.5">
        <li v-for="session in sessions" :key="session.id">
          <NuxtLink
            :to="`/chat/${session.id}`"
            class="grid gap-0.5 rounded-sm border-l-2 px-3 py-2.5 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            :class="session.id === activeId
              ? 'border-forest bg-teal-wash font-semibold text-forest'
              : 'border-transparent text-forest hover:bg-muted'"
            :aria-current="session.id === activeId ? 'page' : undefined"
          >
            <span class="truncate">{{ session.title }}</span>
            <span class="text-xs font-normal text-muted-foreground">{{ formatRelativeTime(session.lastActivityAt) }}</span>
          </NuxtLink>
        </li>
      </ul>
    </div>
    <div v-if="hasMore" class="border-t p-3">
      <Button
        type="button"
        variant="outline"
        size="sm"
        class="w-full"
        :disabled="loadingMore"
        @click="loadMore"
      >
        <ChevronDown aria-hidden="true" />
        Load more
      </Button>
    </div>
  </aside>
</template>
