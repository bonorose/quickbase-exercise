<script setup lang="ts">
import type { TicketStatus } from '~/types/api/responses'

const props = defineProps<{ status: TicketStatus }>()

const styles: Record<TicketStatus, string> = {
  open: 'border-transparent bg-teal-wash text-forest',
  blocked: 'border-signal bg-signal-wash text-forest',
  closed: 'border-transparent bg-rule text-forest',
}

const labels: Record<TicketStatus, string> = {
  open: 'Open',
  blocked: 'Blocked',
  closed: 'Closed',
}
</script>

<template>
  <Badge :class="styles[props.status]">
    {{ labels[props.status] }}
  </Badge>
</template>
