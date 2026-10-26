<script setup lang="ts">
withDefaults(defineProps<{
  wordmark?: boolean
}>(), {
  wordmark: true,
})
</script>

<template>
  <span class="inline-flex items-center gap-2.5 text-forest">
    <svg viewBox="0 0 3 4" class="h-8 w-6 shrink-0" aria-hidden="true">
      <rect x="1" y="0" width="2" height="1" fill="#259B89" />
      <rect x="0" y="1" width="1" height="1" fill="#102D18" />
      <rect x="2" y="1" width="1" height="1" fill="#259B89" />
      <rect x="0" y="2" width="2" height="1" fill="#102D18" />
      <rect x="2" y="3" width="1" height="1" fill="#F45A35" />
    </svg>
    <span v-if="wordmark" class="text-xl font-extrabold leading-none tracking-[-0.045em]">qAI</span>
  </span>
</template>
