<script setup lang="ts">
import type { PendingRevision } from '~/types/api/responses'

defineProps<{
  open: boolean
  draft: PendingRevision | null
  canApprove?: boolean
}>()

const emit = defineEmits<{
  close: []
  updated: [draft: PendingRevision]
  decided: [draft: PendingRevision]
}>()
</script>

<template>
  <Sheet :open="open" @update:open="(value) => { if (!value) emit('close') }">
    <SheetContent side="right" class="w-full overflow-y-auto sm:max-w-xl">
      <SheetHeader>
        <SheetTitle>Review draft</SheetTitle>
        <SheetDescription>
          Save, approve, and reject are separate. Closing this panel leaves the draft open.
        </SheetDescription>
      </SheetHeader>
      <DraftEditor
        v-if="draft"
        :draft="draft"
        :can-approve="canApprove"
        @updated="emit('updated', $event)"
        @decided="emit('decided', $event)"
      />
    </SheetContent>
  </Sheet>
</template>
