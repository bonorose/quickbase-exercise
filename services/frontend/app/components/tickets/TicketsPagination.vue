<script setup lang="ts">
const props = defineProps<{
  page: number
  pageCount: number
}>()

const emit = defineEmits<{
  go: [page: number]
}>()
</script>

<template>
  <Pagination
    :page="props.page"
    :items-per-page="1"
    :total="Math.max(props.pageCount, 1)"
    @update:page="emit('go', $event)"
  >
    <div class="flex w-full items-center justify-between gap-3">
      <p class="text-sm text-muted-foreground">
        Page {{ props.page }} of {{ props.pageCount }}
      </p>
      <PaginationContent>
        <Button
          variant="outline"
          size="sm"
          :disabled="props.page <= 1"
          @click="emit('go', props.page - 1)"
        >
          Previous
        </Button>
        <Button
          variant="outline"
          size="sm"
          :disabled="props.page >= props.pageCount"
          @click="emit('go', props.page + 1)"
        >
          Next
        </Button>
      </PaginationContent>
    </div>
  </Pagination>
</template>
