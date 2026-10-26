<script setup lang="ts">
import type { Component } from 'vue'

defineProps<{
  title: string
  value?: string | number
  description?: string
  icon: Component
  loading?: boolean
}>()
</script>

<template>
  <Card>
    <CardHeader class="flex flex-row items-center justify-between gap-2 pb-2">
      <CardTitle class="text-[11px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
        {{ title }}
      </CardTitle>
      <component :is="icon" class="size-4 text-teal-signal" />
    </CardHeader>
    <CardContent>
      <Skeleton v-if="loading" class="h-8 w-20" />
      <slot v-else>
        <span class="text-3xl font-extrabold tabular-nums tracking-tight">{{ value }}</span>
      </slot>
      <p v-if="description" class="mt-1 text-xs text-muted-foreground">
        {{ description }}
      </p>
    </CardContent>
  </Card>
</template>
