<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { DialogClose, DialogContent, DialogOverlay, DialogPortal } from 'reka-ui'
import { X } from 'lucide-vue-next'
import { cn } from '~/lib/utils'

const props = withDefaults(defineProps<{
  side?: 'right' | 'left'
  class?: HTMLAttributes['class']
  showClose?: boolean
}>(), {
  side: 'right',
  showClose: true,
})
</script>

<template>
  <DialogPortal>
    <DialogOverlay class="fixed inset-0 z-50 bg-forest/40" />
    <DialogContent
      :class="cn(
        'fixed z-50 flex flex-col gap-4 bg-card p-6 outline-none',
        'inset-y-0 h-full w-full sm:max-w-lg',
        props.side === 'right' ? 'right-0 border-l' : 'left-0 border-r',
        props.class,
      )"
    >
      <slot />
      <DialogClose
        v-if="props.showClose"
        class="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring"
      >
        <X class="size-4" />
        <span class="sr-only">Close</span>
      </DialogClose>
    </DialogContent>
  </DialogPortal>
</template>
