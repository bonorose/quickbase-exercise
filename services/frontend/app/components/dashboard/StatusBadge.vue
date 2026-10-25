<script setup lang="ts">
import type { ServiceStatus } from '~/types/models'
import { cn } from '~/lib/utils'

const props = defineProps<{ status: ServiceStatus }>()

const styles: Record<ServiceStatus, { label: string, dot: string }> = {
  up: { label: 'Operational', dot: 'bg-success' },
  degraded: { label: 'Degraded', dot: 'bg-amber-500' },
  down: { label: 'Down', dot: 'bg-destructive' },
}
</script>

<template>
  <span class="inline-flex items-center gap-2">
    <span :class="cn('size-2.5 rounded-full', styles[props.status].dot)" aria-hidden="true" />
    {{ styles[props.status].label }}
  </span>
</template>
