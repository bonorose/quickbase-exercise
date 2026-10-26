<script setup lang="ts">
import { AlertCircle, Loader2 } from 'lucide-vue-next'

const { fields, fieldErrors, formError, submitting, retryIn, submit } = useLoginForm()
</script>

<template>
  <Card>
    <CardHeader>
      <CardTitle class="text-2xl font-extrabold tracking-tight">
        Sign in
      </CardTitle>
      <CardDescription>Enter your email and password to continue.</CardDescription>
    </CardHeader>

    <form novalidate @submit.prevent="submit">
      <CardContent class="grid gap-4">
        <Alert v-if="formError" variant="destructive">
          <AlertCircle />
          <AlertDescription>{{ formError }}</AlertDescription>
        </Alert>

        <div class="grid gap-2">
          <Label for="email">Email</Label>
          <Input
            id="email"
            v-model="fields.email"
            type="email"
            autocomplete="email"
            placeholder="you@example.com"
            :aria-invalid="!!fieldErrors.email"
            :disabled="submitting || retryIn > 0"
          />
          <p v-if="fieldErrors.email" class="flex items-center gap-2 text-sm text-foreground">
            <span class="size-1.5 shrink-0 bg-signal" aria-hidden="true" />
            {{ fieldErrors.email }}
          </p>
        </div>

        <div class="grid gap-2">
          <Label for="password">Password</Label>
          <Input
            id="password"
            v-model="fields.password"
            type="password"
            autocomplete="current-password"
            :aria-invalid="!!fieldErrors.password"
            :disabled="submitting || retryIn > 0"
          />
          <p v-if="fieldErrors.password" class="flex items-center gap-2 text-sm text-foreground">
            <span class="size-1.5 shrink-0 bg-signal" aria-hidden="true" />
            {{ fieldErrors.password }}
          </p>
        </div>
      </CardContent>

      <CardFooter>
        <Button type="submit" class="w-full" :disabled="submitting || retryIn > 0">
          <Loader2 v-if="submitting" class="animate-spin" />
          {{ submitting ? 'Signing in…' : 'Sign in' }}
        </Button>
      </CardFooter>
    </form>
  </Card>
</template>
