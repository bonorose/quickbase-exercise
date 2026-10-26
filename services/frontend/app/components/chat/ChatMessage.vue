<script setup lang="ts">
import { Check } from 'lucide-vue-next'
import type { ChatMessageVM } from '~/services/chat.service'
import type { PendingRevision } from '~/types/api/responses'
import { formatClockTime } from '~/utils/clockTime'
import { inertAssistantText } from '~/utils/sanitize'

const props = defineProps<{
  message: ChatMessageVM
  pendingDraft?: PendingRevision | null
}>()

const emit = defineEmits<{ review: [pendingRevisionId: string] }>()

const systemText = computed(() => {
  const part = props.message.parts.find(item => item.kind === 'text')
  return part?.kind === 'text' ? part.text : ''
})
const time = computed(() => formatClockTime(props.message.createdAt))
const lastTextIndex = computed(() => {
  for (let index = props.message.parts.length - 1; index >= 0; index -= 1) {
    if (props.message.parts[index]?.kind === 'text') return index
  }
  return -1
})

function displayText(text: string) {
  return props.message.role === 'assistant' ? inertAssistantText(text) : text
}
</script>

<template>
  <article
    v-if="message.role === 'system'"
    class="flex justify-center"
    data-role="system"
  >
    <p class="rounded-full bg-muted px-3 py-1 text-xs text-ink">
      {{ systemText }}
    </p>
  </article>

  <article
    v-else-if="message.role === 'user'"
    class="grid justify-items-end gap-2"
    data-role="user"
  >
    <div
      v-for="(part, index) in message.parts"
      :key="`${message.id}-text-${index}`"
      class="max-w-[36rem] rounded-sm bg-forest px-4 py-2.5 text-sm text-primary-foreground shadow-sm"
    >
      <p v-if="part.kind === 'text'" class="whitespace-pre-wrap break-words">{{ part.text }}</p>
    </div>
    <p class="flex items-center gap-1.5 font-mono text-[11px] text-muted-foreground">
      <time :datetime="message.createdAt.toISOString()">{{ time }}</time>
      <Check class="size-3.5 text-teal-signal" aria-label="Sent" />
    </p>
  </article>

  <article
    v-else
    class="flex gap-3"
    data-role="assistant"
  >
    <span class="mt-1 flex size-8 shrink-0 items-center justify-center rounded-sm border bg-card" aria-hidden="true">
      <BrandMark :wordmark="false" class="scale-[0.6]" />
    </span>
    <div class="grid min-w-0 flex-1 justify-items-start gap-2">
      <template v-for="(part, index) in message.parts" :key="part.kind === 'tool' ? part.call_id : `${message.id}-text-${index}`">
        <div v-if="part.kind === 'text'" class="w-full max-w-[40rem] rounded-sm border bg-card px-4 py-3 text-sm shadow-sm">
          <p class="whitespace-pre-wrap break-words leading-relaxed">{{ displayText(part.text) }}</p>
          <div
            v-if="index === lastTextIndex"
            class="mt-2 flex items-center justify-between gap-3 font-mono text-[11px] text-muted-foreground"
          >
            <span>{{ message.model ?? '' }}</span>
            <time :datetime="message.createdAt.toISOString()">{{ time }}</time>
          </div>
        </div>
        <div v-else class="w-full max-w-[40rem]">
          <ToolCallTrace
            :part="part"
            :time="message.createdAt"
            :draft="pendingDraft"
            @review="emit('review', $event)"
          />
        </div>
      </template>
      <Alert v-if="message.error" variant="destructive" class="max-w-[40rem]">
        <AlertDescription>{{ message.error.message }}</AlertDescription>
      </Alert>
      <p v-if="message.stopped" class="text-xs text-muted-foreground">
        Stopped
      </p>
    </div>
  </article>
</template>
