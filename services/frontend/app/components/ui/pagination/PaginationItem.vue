<script setup lang="ts">
import type { PaginationListItemProps } from 'reka-ui'
import { PaginationListItem } from 'reka-ui'

const props = defineProps<PaginationListItemProps>()
</script>

<template>
  <PaginationListItem v-bind="props">
    <slot />
  </PaginationListItem>
</template>
