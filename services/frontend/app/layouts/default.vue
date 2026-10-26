<script setup lang="ts">
const mobileOpen = ref(false)
const route = useRoute()
const fullBleed = computed(() => route.meta.fullBleed === true)
</script>

<template>
  <TooltipProvider>
    <a
      href="#main"
      class="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:bg-card focus:px-3 focus:py-2 focus:ring-1 focus:ring-ring"
    >
      Skip to content
    </a>
    <div class="flex bg-background" :class="fullBleed ? 'h-screen overflow-hidden' : 'min-h-screen'">
      <aside class="hidden w-56 shrink-0 border-r bg-card p-4 lg:block">
        <p class="mb-4 py-1 pl-[14px] pr-3 text-[11px] font-medium uppercase tracking-[0.16em] text-forest">
          Navigation
        </p>
        <AppNav />
      </aside>

      <Sheet :open="mobileOpen" @update:open="mobileOpen = $event">
        <SheetContent side="left" class="w-64 p-4">
          <SheetHeader>
            <SheetTitle>Navigation</SheetTitle>
          </SheetHeader>
          <Separator class="my-3" />
          <AppNav :on-navigate="() => { mobileOpen = false }" />
        </SheetContent>
      </Sheet>

      <div class="flex min-h-0 min-w-0 flex-1 flex-col">
        <AppHeader v-model:mobile-open="mobileOpen" />
        <main
          id="main"
          class="w-full flex-1"
          :class="fullBleed ? 'flex min-h-0 flex-col' : 'mx-auto max-w-6xl px-4 py-8 sm:px-6'"
        >
          <slot />
        </main>
      </div>
    </div>
  </TooltipProvider>
</template>
