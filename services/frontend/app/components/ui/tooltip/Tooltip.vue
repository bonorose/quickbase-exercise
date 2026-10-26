<script setup lang="ts">
import { TooltipRoot, type TooltipRootProps } from 'reka-ui'

const props = defineProps<TooltipRootProps>()
</script>

<template>
  <TooltipRoot v-bind="props">
    <slot />
  </TooltipRoot>
</template>
