<script setup lang="ts">
defineProps<{
  status: string | null
  streaming: boolean
  showTyping: boolean
}>()
</script>

<template>
  <p
    class="flex min-h-5 items-center gap-2 text-sm text-ink"
    aria-live="polite"
    data-testid="stream-status"
  >
    <span
      v-if="status || (streaming && showTyping)"
      class="size-2 shrink-0 animate-pulse rounded-full bg-teal-signal motion-reduce:animate-none"
      aria-hidden="true"
    />
    <template v-if="status">{{ status }}</template>
    <template v-else-if="streaming && showTyping">Thinking…</template>
  </p>
</template>
