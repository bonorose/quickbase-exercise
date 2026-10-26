<template>
  <main class="flex min-h-screen items-center justify-center bg-background px-4 py-12">
    <div class="grid w-full max-w-sm justify-items-center gap-8">
      <div class="grid justify-items-center gap-4 text-center">
        <BrandMark />
        <p class="font-serif text-3xl font-semibold leading-tight text-forest">
          Ticket Intelligence
        </p>
      </div>
      <div class="w-full">
        <slot />
      </div>
    </div>
  </main>
</template>
