<script setup lang="ts">
import { AlertCircle, Loader2 } from 'lucide-vue-next'

const { fields, fieldErrors, formError, submitting, submit } = useLoginForm()
</script>

<template>
  <Card>
    <CardHeader>
      <CardTitle class="text-xl">
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
            :disabled="submitting"
          />
          <p v-if="fieldErrors.email" class="text-sm text-destructive">
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
            :disabled="submitting"
          />
          <p v-if="fieldErrors.password" class="text-sm text-destructive">
            {{ fieldErrors.password }}
          </p>
        </div>
      </CardContent>

      <CardFooter>
        <Button type="submit" class="w-full" :disabled="submitting">
          <Loader2 v-if="submitting" class="animate-spin" />
          {{ submitting ? 'Signing in…' : 'Sign in' }}
        </Button>
      </CardFooter>
    </form>
  </Card>
</template>
