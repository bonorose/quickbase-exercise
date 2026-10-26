<script setup lang="ts">
import { SendHorizontal, Square } from 'lucide-vue-next'

const props = defineProps<{
  canSend: boolean
  streaming: boolean
  showExamples: boolean
  /** The model that answered last, shown for context. There is no model picker. */
  model?: string | null
}>()

const emit = defineEmits<{
  send: [text: string]
  stop: []
}>()

const MAX = 4000
const WARN_FROM = 3500
const draft = ref('')
const fieldId = 'chat-composer'
const hintId = 'chat-composer-hint'

const length = computed(() => draft.value.length)
const overLimit = computed(() => length.value > MAX)
const nearLimit = computed(() => length.value >= WARN_FROM)
const sendable = computed(() => props.canSend && !props.streaming && draft.value.trim().length > 0 && !overLimit.value)

const examples = [
  'What\'s blocked on billing?',
  'Summarize open tickets',
]

function submit() {
  if (props.streaming) return
  if (!sendable.value) return
  emit('send', draft.value)
  draft.value = ''
}

function onKeydown(event: KeyboardEvent) {
  if (event.key !== 'Enter' || event.shiftKey) return
  event.preventDefault()
  submit()
}

function useExample(prompt: string) {
  draft.value = prompt
}
</script>

<template>
  <form class="grid gap-2" @submit.prevent="submit">
    <div v-if="showExamples" class="flex flex-wrap gap-2">
      <Button
        v-for="prompt in examples"
        :key="prompt"
        type="button"
        variant="outline"
        size="sm"
        class="bg-card"
        @click="useExample(prompt)"
      >
        {{ prompt }}
      </Button>
    </div>
    <div class="rounded-sm border bg-card shadow-sm focus-within:ring-1 focus-within:ring-ring">
      <label :for="fieldId" class="sr-only">Message</label>
      <textarea
        :id="fieldId"
        v-model="draft"
        data-testid="chat-composer"
        rows="2"
        :maxlength="MAX"
        placeholder="Ask about your team's tickets…"
        class="block max-h-48 min-h-16 w-full resize-none bg-transparent px-4 pt-3 text-sm placeholder:text-muted-foreground focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50"
        :aria-describedby="hintId"
        :aria-invalid="overLimit"
        @keydown="onKeydown"
      />
      <div class="flex items-center justify-between gap-3 px-3 pb-3 pt-1">
        <span class="truncate font-mono text-[11px] text-muted-foreground">
          <template v-if="model">Model: {{ model }}</template>
        </span>
        <div class="flex items-center gap-3">
          <span
            class="font-mono text-[11px]"
            :class="overLimit || nearLimit ? 'text-signal' : 'text-muted-foreground'"
            aria-hidden="true"
          >{{ length }} / {{ MAX }}</span>
          <Button
            v-if="streaming"
            type="button"
            variant="outline"
            data-testid="chat-stop"
            @click="emit('stop')"
          >
            <Square aria-hidden="true" />
            Stop
          </Button>
          <Button v-else type="submit" data-testid="chat-send" :disabled="!sendable">
            <SendHorizontal aria-hidden="true" />
            Send
          </Button>
        </div>
      </div>
    </div>
    <p :id="hintId" class="text-right text-[11px] text-muted-foreground">
      Enter to send · Shift+Enter for a new line
      <span class="sr-only">. Up to {{ MAX }} characters, {{ length }} used.</span>
    </p>
  </form>
</template>
