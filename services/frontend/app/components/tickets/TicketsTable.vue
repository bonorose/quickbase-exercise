<script setup lang="ts">
import type { TicketRow } from '~/types/models'
import { formatRelativeTime } from '~/utils/relativeTime'

defineProps<{
  rows: TicketRow[]
  loading?: boolean
}>()

const emit = defineEmits<{
  select: [id: number]
}>()
</script>

<template>
  <Table>
    <TableHeader>
      <TableRow>
        <TableHead class="w-20">
          ID
        </TableHead>
        <TableHead>Title</TableHead>
        <TableHead>Status</TableHead>
        <TableHead>Priority</TableHead>
        <TableHead class="text-right">
          Updated
        </TableHead>
      </TableRow>
    </TableHeader>
    <TableBody>
      <template v-if="loading">
        <TableRow v-for="n in 5" :key="n">
          <TableCell v-for="c in 5" :key="c">
            <Skeleton class="h-4 w-full" />
          </TableCell>
        </TableRow>
      </template>
      <TableRow
        v-for="row in rows"
        v-else
        :key="row.id"
        class="cursor-pointer"
        tabindex="0"
        @click="emit('select', row.id)"
        @keydown.enter.prevent="emit('select', row.id)"
        @keydown.space.prevent="emit('select', row.id)"
      >
        <TableCell class="font-mono text-xs text-muted-foreground">
          {{ row.id }}
        </TableCell>
        <TableCell class="font-medium">
          <button
            type="button"
            class="text-left font-medium focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            @click.stop="emit('select', row.id)"
          >
            {{ row.title }}
          </button>
        </TableCell>
        <TableCell>
          <StatusBadge :status="row.status" />
        </TableCell>
        <TableCell>
          <PriorityBadge :priority="row.priority" />
        </TableCell>
        <TableCell class="text-right font-mono text-xs text-muted-foreground">
          {{ formatRelativeTime(row.updatedAt) }}
        </TableCell>
      </TableRow>
    </TableBody>
  </Table>
</template>
