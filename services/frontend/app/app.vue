<script setup lang="ts">
import { Toaster } from 'vue-sonner'
const { organization } = useAuth()

useHead({
  titleTemplate: (title) => {
    const org = organization.value?.name
    const suffix = org ? `${org} — qAI` : 'qAI'
    return title ? `${title} — ${suffix}` : suffix
  },
  htmlAttrs: { lang: 'en' },
})
</script>

<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
  <Toaster position="top-right" />
</template>
