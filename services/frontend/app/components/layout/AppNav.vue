<script setup lang="ts">
import { isNavItemActive, navItemsFor } from '~/utils/navItems'

const route = useRoute()
const { role } = useAuth()
const visible = computed(() => navItemsFor(role.value))

function isActive(to: string) {
  return isNavItemActive(route.path, to)
}

defineProps<{
  onNavigate?: () => void
}>()
</script>

<template>
  <nav aria-label="Main" class="grid gap-1">
    <NuxtLink
      v-for="item in visible"
      :key="item.to"
      :to="item.to"
      :aria-current="isActive(item.to) ? 'page' : undefined"
      class="flex items-center gap-2 border-l-2 px-3 py-2 text-sm hover:bg-teal-wash hover:text-forest focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
      :class="isActive(item.to) ? 'border-teal-signal bg-teal-wash font-medium text-forest' : 'border-transparent text-ink'"
      @click="onNavigate?.()"
    >
      <component :is="item.icon" class="size-4" aria-hidden="true" />
      {{ item.label }}
    </NuxtLink>
  </nav>
</template>
