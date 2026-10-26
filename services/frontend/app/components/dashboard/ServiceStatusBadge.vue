<script setup lang="ts">
import type { ServiceStatus } from '~/types/models'
import { cn } from '~/lib/utils'

const props = defineProps<{ status: ServiceStatus }>()

const styles: Record<ServiceStatus, { label: string, dot: string }> = {
  up: { label: 'Operational', dot: 'bg-teal-signal' },
  degraded: { label: 'Degraded', dot: 'bg-signal' },
  down: { label: 'Down', dot: 'bg-forest' },
}
</script>

<template>
  <span class="inline-flex items-center gap-2 text-lg font-semibold tracking-tight">
    <span :class="cn('size-2 shrink-0', styles[props.status].dot)" aria-hidden="true" />
    {{ styles[props.status].label }}
  </span>
</template>
