<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '~/lib/utils'

const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <th :class="cn('h-10 px-2 text-left align-middle text-[11px] font-medium uppercase tracking-[0.14em] text-muted-foreground', props.class)">
    <slot />
  </th>
</template>
