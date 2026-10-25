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
      <CardTitle class="text-sm font-medium text-muted-foreground">
        {{ title }}
      </CardTitle>
      <component :is="icon" class="size-4 text-muted-foreground" />
    </CardHeader>
    <CardContent>
      <Skeleton v-if="loading" class="h-8 w-20" />
      <div v-else class="text-2xl font-bold tabular-nums">
        <slot>{{ value }}</slot>
      </div>
      <p v-if="description" class="mt-1 text-xs text-muted-foreground">
        {{ description }}
      </p>
    </CardContent>
  </Card>
</template>
