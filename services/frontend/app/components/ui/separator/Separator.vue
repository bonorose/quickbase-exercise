<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { Separator } from 'reka-ui'
import { cn } from '~/lib/utils'

const props = withDefaults(defineProps<{
  orientation?: 'horizontal' | 'vertical'
  class?: HTMLAttributes['class']
}>(), {
  orientation: 'horizontal',
})
</script>

<template>
  <Separator
    :orientation="props.orientation"
    :class="cn(
      'shrink-0 bg-border',
      props.orientation === 'horizontal' ? 'h-px w-full' : 'h-full w-px',
      props.class,
    )"
  />
</template>
