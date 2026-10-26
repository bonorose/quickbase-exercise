<script setup lang="ts">
import type { RevisionView } from '~/types/models'
import { ticketFieldLabel } from '~/utils/ticketFieldLabels'
import { formatRelativeTime } from '~/utils/relativeTime'

defineProps<{
  revisions: RevisionView[]
}>()
</script>

<template>
  <ol class="grid gap-4">
    <li v-if="revisions.length === 0" class="text-sm text-muted-foreground">
      No revisions yet.
    </li>
    <li v-for="revision in revisions" :key="revision.id" class="grid gap-1 border-l-2 border-rule pl-3">
      <p class="text-sm font-medium">
        {{ revision.authorName }}
        <span class="font-mono text-xs font-medium text-muted-foreground">
          · {{ formatRelativeTime(revision.createdAt) }}
        </span>
      </p>
      <ul class="grid gap-0.5 text-sm">
        <li v-for="change in revision.changes" :key="change.field">
          <span class="text-muted-foreground">{{ ticketFieldLabel(change.field) }}:</span>
          {{ change.from }} → {{ change.to }}
        </li>
        <li v-if="revision.changes.length === 0" class="text-muted-foreground">
          No field changes recorded.
        </li>
      </ul>
    </li>
  </ol>
</template>
