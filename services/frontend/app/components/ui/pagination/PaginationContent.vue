<script setup lang="ts">
import type { PaginationListProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { PaginationList } from 'reka-ui'
import { cn } from '~/lib/utils'

const props = defineProps<PaginationListProps & { class?: HTMLAttributes['class'] }>()
</script>

<template>
  <PaginationList v-bind="props" :class="cn('flex flex-row items-center gap-2', props.class)">
    <slot />
  </PaginationList>
</template>
