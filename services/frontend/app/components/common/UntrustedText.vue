<script setup lang="ts">
import { useResizeObserver } from '@vueuse/core'
import { isDisplayTruncated, truncateForDisplay } from '~/utils/sanitize'

const props = withDefaults(defineProps<{
  text: string
  lines?: number
  label?: string
  showLabel?: boolean
}>(), {
  lines: 6,
  label: 'External content',
  showLabel: true,
})

const expanded = ref(false)
const overflow = ref(false)
const body = ref<HTMLElement | null>(null)

const display = computed(() => truncateForDisplay(props.text))
const truncated = computed(() => isDisplayTruncated(props.text))

function measure() {
  const node = body.value
  if (!node || expanded.value) return
  overflow.value = node.scrollHeight > node.clientHeight + 1
}

onMounted(() => nextTick(measure))
watch(() => props.text, () => nextTick(measure))
useResizeObserver(body, measure)
</script>

<template>
  <div class="grid gap-1.5">
    <p
      v-if="props.showLabel && props.label"
      class="text-[11px] font-medium uppercase tracking-[0.14em] text-muted-foreground"
    >
      {{ props.label }}
    </p>
    <div
      ref="body"
      class="whitespace-pre-wrap break-words text-sm"
      :class="expanded ? '' : 'overflow-hidden'"
      :style="expanded ? undefined : { display: '-webkit-box', WebkitLineClamp: props.lines, WebkitBoxOrient: 'vertical' }"
    >{{ display }}</div>
    <p v-if="truncated" class="text-xs text-muted-foreground">
      (truncated)
    </p>
    <Button
      v-if="overflow || expanded"
      variant="link"
      size="sm"
      class="h-auto justify-start px-0"
      @click="expanded = !expanded"
    >
      {{ expanded ? 'Show less' : 'Show more' }}
    </Button>
  </div>
</template>
