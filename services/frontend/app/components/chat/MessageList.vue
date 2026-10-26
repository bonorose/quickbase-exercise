<script setup lang="ts">
import { ArrowDown } from 'lucide-vue-next'
import type { ChatMessageVM } from '~/services/chat.service'
import type { PendingRevision } from '~/types/api/responses'

const props = defineProps<{
  messages: ChatMessageVM[]
  streaming: boolean
  pendingDraft?: PendingRevision | null
}>()

const emit = defineEmits<{ review: [pendingRevisionId: string] }>()

const scroller = ref<HTMLElement | null>(null)
const pinned = ref(true)

function distanceFromBottom(element: HTMLElement) {
  return element.scrollHeight - element.scrollTop - element.clientHeight
}

function onScroll() {
  const element = scroller.value
  if (!element) return
  pinned.value = distanceFromBottom(element) < 48
}

function jumpToLatest() {
  const element = scroller.value
  if (!element) return
  element.scrollTo({ top: element.scrollHeight })
  pinned.value = true
}

watch(() => [props.messages, props.streaming], async () => {
  await nextTick()
  if (pinned.value) jumpToLatest()
}, { deep: true })
</script>

<template>
  <div class="relative min-h-0 flex-1">
    <div
      ref="scroller"
      data-testid="message-list"
      class="absolute inset-0 overflow-y-auto px-6 py-6"
      role="log"
      aria-live="off"
      :aria-busy="streaming"
      @scroll="onScroll"
    >
      <div class="mx-auto grid max-w-3xl gap-5">
        <ChatMessage
          v-for="message in messages"
          :key="message.id"
          :message="message"
          :pending-draft="pendingDraft"
          @review="emit('review', $event)"
        />
        <slot name="after" />
      </div>
    </div>
    <Button
      v-if="!pinned"
      type="button"
      variant="outline"
      size="sm"
      class="absolute bottom-3 left-1/2 -translate-x-1/2 bg-card shadow-sm"
      @click="jumpToLatest"
    >
      <ArrowDown aria-hidden="true" />
      Jump to latest
    </Button>
  </div>
</template>
