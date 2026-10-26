<script setup lang="ts">
import type { DiscussionView } from '~/types/models'

defineProps<{
  discussions: DiscussionView[]
}>()
</script>

<template>
  <ol class="grid gap-4">
    <li v-if="discussions.length === 0" class="text-sm text-muted-foreground">
      No discussions yet.
    </li>
    <li v-for="discussion in discussions" :key="discussion.id" class="grid gap-1">
      <p class="text-sm font-medium">
        {{ discussion.authorName }}
      </p>
      <UntrustedText :text="discussion.contents" :lines="4" label="Discussion" :show-label="false" />
    </li>
  </ol>
</template>
