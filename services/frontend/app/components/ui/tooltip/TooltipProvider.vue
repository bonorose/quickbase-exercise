<script setup lang="ts">
import { TooltipProvider } from 'reka-ui'

const props = withDefaults(defineProps<{
  delayDuration?: number
}>(), {
  delayDuration: 200,
})
</script>

<template>
  <TooltipProvider :delay-duration="props.delayDuration">
    <slot />
  </TooltipProvider>
</template>
