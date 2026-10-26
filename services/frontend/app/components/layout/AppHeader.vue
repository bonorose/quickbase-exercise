<script setup lang="ts">
import { LogOut, Menu } from 'lucide-vue-next'
import { organizationBadgeClass } from '~/utils/organizationTheme'

const { user, organization, role, logout } = useAuth()
const mobileOpen = defineModel<boolean>('mobileOpen', { default: false })

const roleLabel = computed(() => {
  if (role.value === 'team_lead') return 'Team lead'
  if (role.value === 'operator') return 'Operator'
  return null
})
</script>

<template>
  <header class="border-b bg-card">
    <div class="flex h-16 items-center justify-between gap-3 px-4 sm:px-6">
      <div class="flex min-w-0 items-center gap-3">
        <Button
          class="lg:hidden"
          variant="ghost"
          size="icon"
          aria-label="Open navigation"
          @click="mobileOpen = true"
        >
          <Menu />
        </Button>
        <NuxtLink to="/" class="shrink-0">
          <BrandMark />
        </NuxtLink>
        <TooltipProvider v-if="organization">
          <Tooltip>
            <TooltipTrigger>
              <Badge
                data-testid="tenant-badge"
                :class="['max-w-36 truncate sm:max-w-56', organizationBadgeClass(organization.name)]"
              >
                {{ organization.name }}
              </Badge>
            </TooltipTrigger>
            <TooltipContent>{{ organization.name }}</TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      <div v-if="user" class="flex min-w-0 items-center gap-3">
        <div class="hidden min-w-0 text-right text-sm leading-tight sm:block">
          <p class="truncate font-medium">
            {{ user.fullName }}
          </p>
          <p class="truncate text-muted-foreground">
            {{ roleLabel ?? user.email }}
          </p>
        </div>
        <span
          class="flex size-8 shrink-0 items-center justify-center bg-forest text-xs font-medium text-white"
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
