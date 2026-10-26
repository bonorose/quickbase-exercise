<script setup lang="ts">
import { FileQuestion } from 'lucide-vue-next'

withDefaults(defineProps<{
  resource?: string
  to?: string
  linkLabel?: string
}>(), {
  resource: 'resource',
  to: '/',
  linkLabel: 'Back to the list',
})
</script>

<template>
  <div class="grid justify-items-start gap-3 py-6" data-testid="not-found-state">
    <FileQuestion class="size-8 text-muted-foreground" aria-hidden="true" />
    <div class="grid gap-1">
      <h2 class="text-lg font-semibold">
        We couldn't find that {{ resource }}
      </h2>
      <p class="text-sm text-muted-foreground">
        It may have been removed, or the link is no longer valid.
      </p>
    </div>
    <Button as-child variant="outline" size="sm">
      <NuxtLink :to="to">
        {{ linkLabel }}
      </NuxtLink>
    </Button>
  </div>
</template>
