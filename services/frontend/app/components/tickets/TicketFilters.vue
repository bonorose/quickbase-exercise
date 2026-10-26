<script setup lang="ts">
import type { TicketPriority, TicketSort, TicketStatus } from '~/types/api/responses'

const ALL = 'all'

const qInput = defineModel<string>('q', { required: true })

const props = defineProps<{
  status?: TicketStatus
  priority?: TicketPriority
  sort: TicketSort
}>()

const emit = defineEmits<{
  filter: [value: { status?: TicketStatus | '', priority?: TicketPriority | '', sort?: TicketSort }]
}>()

function asStatus(value: unknown): TicketStatus | '' {
  return value === ALL || value == null ? '' : value as TicketStatus
}

function asPriority(value: unknown): TicketPriority | '' {
  return value === ALL || value == null ? '' : value as TicketPriority
}
</script>

<template>
  <div class="flex flex-wrap items-end gap-3">
    <div class="grid min-w-56 flex-1 gap-1.5">
      <Label for="ticket-search">Search</Label>
      <Input
        id="ticket-search"
        v-model="qInput"
        type="search"
        placeholder="Search titles…"
      />
    </div>
    <div class="grid min-w-36 gap-1.5">
      <Label for="ticket-status">Status</Label>
      <Select
        :model-value="props.status ?? ALL"
        @update:model-value="emit('filter', { status: asStatus($event) })"
      >
        <SelectTrigger id="ticket-status">
          <SelectValue placeholder="All" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem :value="ALL">
            All
          </SelectItem>
          <SelectItem value="open">
            Open
          </SelectItem>
          <SelectItem value="blocked">
            Blocked
          </SelectItem>
          <SelectItem value="closed">
            Closed
          </SelectItem>
        </SelectContent>
      </Select>
    </div>
    <div class="grid min-w-36 gap-1.5">
      <Label for="ticket-priority">Priority</Label>
      <Select
        :model-value="props.priority ?? ALL"
        @update:model-value="emit('filter', { priority: asPriority($event) })"
      >
        <SelectTrigger id="ticket-priority">
          <SelectValue placeholder="All" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem :value="ALL">
            All
          </SelectItem>
          <SelectItem value="lowest">
            Lowest
          </SelectItem>
          <SelectItem value="low">
            Low
          </SelectItem>
          <SelectItem value="medium">
            Medium
          </SelectItem>
          <SelectItem value="high">
            High
          </SelectItem>
          <SelectItem value="critical">
            Critical
          </SelectItem>
        </SelectContent>
      </Select>
    </div>
    <div class="grid min-w-48 gap-1.5">
      <Label for="ticket-sort">Sort</Label>
      <Select
        :model-value="props.sort"
        @update:model-value="emit('filter', { sort: $event as TicketSort })"
      >
        <SelectTrigger id="ticket-sort">
          <SelectValue placeholder="Updated (newest)" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="-date_updated">
            Updated (newest)
          </SelectItem>
          <SelectItem value="date_updated">
            Updated (oldest)
          </SelectItem>
          <SelectItem value="priority">
            Priority (lowest first)
          </SelectItem>
          <SelectItem value="-priority">
            Priority (highest first)
          </SelectItem>
          <SelectItem value="id">
            ID
          </SelectItem>
        </SelectContent>
      </Select>
    </div>
  </div>
</template>
