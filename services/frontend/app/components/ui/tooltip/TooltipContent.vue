<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { TooltipArrow, TooltipContent, TooltipPortal } from 'reka-ui'
import { cn } from '~/lib/utils'

const props = defineProps<{
  class?: HTMLAttributes['class']
  side?: 'top' | 'right' | 'bottom' | 'left'
}>()
</script>

<template>
  <TooltipPortal>
    <TooltipContent
      :side="props.side ?? 'top'"
      :class="cn(
        'z-50 overflow-hidden rounded-md bg-primary px-3 py-1.5 text-xs text-primary-foreground',
        props.class,
      )"
    >
      <slot />
      <TooltipArrow class="fill-primary" />
    </TooltipContent>
  </TooltipPortal>
</template>
