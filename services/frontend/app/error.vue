<script setup lang="ts">
import type { NuxtError } from '#app'

defineProps<{ error: NuxtError }>()

function reload() {
  clearError({ redirect: '/' })
}
</script>

<template>
  <main class="mx-auto grid min-h-screen max-w-lg place-content-center gap-4 px-6 text-center">
    <h1 class="font-serif text-3xl text-forest">
      Something went wrong
    </h1>
    <p class="text-sm text-muted-foreground">
      {{ error.statusCode }} {{ error.message }}
    </p>
    <div class="flex justify-center gap-3">
      <Button type="button" @click="reload">
        Reload
      </Button>
      <Button type="button" variant="outline" @click="clearError({ redirect: '/' })">
        Go to dashboard
      </Button>
    </div>
  </main>
</template>
