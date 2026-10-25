<script setup lang="ts">
import type { LabelProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { Label } from 'reka-ui'
import { cn } from '~/lib/utils'

const props = defineProps<LabelProps & { class?: HTMLAttributes['class'] }>()
</script>

<template>
  <Label
    v-bind="props"
    :class="cn('flex items-center gap-2 text-sm font-medium leading-none select-none peer-disabled:cursor-not-allowed peer-disabled:opacity-50', props.class)"
  >
    <slot />
  </Label>
</template>
