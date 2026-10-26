<script setup lang="ts">
import type { TicketPriority } from '~/types/api/responses'

const props = defineProps<{ priority: TicketPriority }>()

const styles: Record<TicketPriority, string> = {
  lowest: 'border-rule bg-paper text-ink',
  low: 'border-transparent bg-rule text-forest',
  medium: 'border-transparent bg-teal-wash text-forest',
  high: 'border-transparent bg-forest text-white',
  critical: 'border-signal bg-signal-wash text-forest',
}

const labels: Record<TicketPriority, string> = {
  lowest: 'Lowest',
  low: 'Low',
  medium: 'Medium',
  high: 'High',
  critical: 'Critical',
}
</script>

<template>
  <Badge :class="styles[props.priority]">
    {{ labels[props.priority] }}
  </Badge>
</template>
