<template>
  <div class="flex min-h-screen flex-col bg-muted/40">
    <AppHeader />
    <main class="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6">
      <slot />
    </main>
  </div>
</template>
