<script setup lang="ts">
import { LayoutDashboard, LogOut } from 'lucide-vue-next'

const { user, logout } = useAuth()
</script>

<template>
  <header class="border-b bg-background">
    <div class="mx-auto flex h-14 max-w-6xl items-center justify-between px-4 sm:px-6">
      <NuxtLink to="/" class="flex items-center gap-2 font-semibold">
        <LayoutDashboard class="size-5" />
        <span>Quickbase Interview</span>
      </NuxtLink>

      <div v-if="user" class="flex items-center gap-3">
        <div class="hidden text-right text-sm leading-tight sm:block">
          <p class="font-medium">
            {{ user.fullName }}
          </p>
          <p class="text-muted-foreground">
            {{ user.email }}
          </p>
        </div>
        <span
          class="flex size-8 items-center justify-center rounded-full bg-primary text-xs font-semibold text-primary-foreground"
          aria-hidden="true"
        >
          {{ user.initials }}
        </span>
        <Button variant="ghost" size="sm" @click="logout">
          <LogOut />
          Sign out
        </Button>
      </div>
    </div>
  </header>
</template>
