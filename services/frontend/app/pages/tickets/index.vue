<script setup lang="ts">
import { AlertCircle } from 'lucide-vue-next'

useHead({ title: 'Tickets' })

const {
  qInput,
  status,
  priority,
  sort,
  page,
  pageCount,
  selectedId,
  rows,
  total,
  loading,
  errorMessage,
  setFilter,
  goToPage,
  openTicket,
  closeTicket,
  clearFilters,
} = useTicketList()
</script>

<template>
  <div class="grid gap-6">
    <div>
      <h1 class="text-3xl font-extrabold tracking-tight text-forest">
        Tickets
      </h1>
      <p class="text-muted-foreground">
        Your team's queue.
      </p>
    </div>

    <TicketFilters
      v-model:q="qInput"
      :status="status"
      :priority="priority"
      :sort="sort"
      @filter="setFilter"
    />

    <Alert v-if="errorMessage" variant="destructive">
      <AlertCircle />
      <AlertDescription>{{ errorMessage }}</AlertDescription>
    </Alert>

    <Card>
      <CardContent class="pt-6">
        <div v-if="!loading && total === 0" class="grid justify-items-start gap-3 py-10 text-center sm:justify-items-center">
          <p class="text-muted-foreground">
            No tickets match these filters
          </p>
          <Button variant="outline" size="sm" @click="clearFilters">
            Clear filters
          </Button>
        </div>
        <TicketsTable
          v-else
          :rows="rows"
          :loading="loading"
          @select="openTicket"
        />
      </CardContent>
    </Card>

    <TicketsPagination
      v-if="total > 0"
      :page="page"
      :page-count="pageCount"
      @go="goToPage"
    />

    <TicketDrawer :ticket-id="selectedId" @close="closeTicket" />
  </div>
</template>
