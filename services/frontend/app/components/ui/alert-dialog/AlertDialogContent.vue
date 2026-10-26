<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { AlertDialogContent, AlertDialogOverlay, AlertDialogPortal } from 'reka-ui'
import { cn } from '~/lib/utils'

defineOptions({ inheritAttrs: false })

const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template>
  <AlertDialogPortal>
    <AlertDialogOverlay class="fixed inset-0 z-50 bg-forest/40" />
    <!-- Alert dialogs ignore outside clicks; Escape is blocked too, so only an explicit button closes it. -->
    <AlertDialogContent
      v-bind="$attrs"
      :class="cn(
        'fixed left-1/2 top-1/2 z-50 grid max-h-[90vh] w-full max-w-xl -translate-x-1/2 -translate-y-1/2 gap-4 overflow-y-auto rounded-sm border bg-card p-6 shadow-lg outline-none',
        props.class,
      )"
      @escape-key-down="(event: KeyboardEvent) => event.preventDefault()"
    >
      <slot />
    </AlertDialogContent>
  </AlertDialogPortal>
</template>
