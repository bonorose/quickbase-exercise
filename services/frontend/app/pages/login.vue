<script setup lang="ts">
definePageMeta({
  layout: 'auth',
  // The only page reachable without a session (see middleware/auth.global.ts)
  public: true,
})

useHead({ title: 'Sign in' })
</script>

<template>
  <LoginForm />
</template>
