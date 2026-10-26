<script setup lang="ts">
import { ShieldCheck } from 'lucide-vue-next'
import type { PendingRevision } from '~/types/api/responses'

defineProps<{
  open: boolean
  draft: PendingRevision | null
  canApprove: boolean
  needsLead: boolean
}>()

const emit = defineEmits<{
  later: []
  updated: [draft: PendingRevision]
  decided: [draft: PendingRevision]
}>()
</script>

<template>
  <AlertDialog :open="open && draft != null">
    <AlertDialogContent data-testid="approval-modal">
      <AlertDialogHeader>
        <AlertDialogTitle class="flex items-center gap-2">
          <ShieldCheck class="size-5 text-forest" aria-hidden="true" />
          Approve this change?
        </AlertDialogTitle>
        <AlertDialogDescription v-if="draft">
          The assistant drafted a change to ticket #{{ draft.ticket.id }} "{{ draft.ticket.title }}".
          Nothing changes until it's approved.
        </AlertDialogDescription>
      </AlertDialogHeader>

      <DraftEditor
        v-if="draft"
        :draft="draft"
        :can-approve="canApprove"
        @updated="emit('updated', $event)"
        @decided="emit('decided', $event)"
      />

      <AlertDialogFooter class="border-t pt-4">
        <Button type="button" variant="ghost" data-testid="approval-later" @click="emit('later')">
          {{ needsLead ? 'Leave for team lead' : 'Decide later' }}
        </Button>
      </AlertDialogFooter>
    </AlertDialogContent>
  </AlertDialog>
</template>
