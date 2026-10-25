<script setup lang="ts">
useHead({
  titleTemplate: title => (title ? `${title} — Quickbase Interview` : 'Quickbase Interview'),
  htmlAttrs: { lang: 'en' },
})
</script>

<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>
