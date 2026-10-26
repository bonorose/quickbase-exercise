<script setup lang="ts">
  import type { HTMLAttributes } from 'vue'
  import { useVModel } from '@vueuse/core'
  import { cn } from '~/lib/utils'

  const props = defineProps<{
    defaultValue?: string | number
    modelValue?: string | number
    class?: HTMLAttributes['class']
  }>()

  const emits = defineEmits<{
    (e: 'update:modelValue', payload: string | number): void
  }>()

  const modelValue = useVModel(props, 'modelValue', emits, {
    passive: true,
    defaultValue: props.defaultValue,
  })

  defineOptions({ inheritAttrs: false })
</script>

<template>
  <input
    v-model="modelValue"
    v-bind="$attrs"
    :class="
      cn(
        'flex h-9 w-full rounded-sm border border-input bg-card px-3 py-1 text-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring aria-invalid:border-signal aria-invalid:ring-signal disabled:cursor-not-allowed disabled:opacity-50',
        props.class
      )
    "
  >
</template>
