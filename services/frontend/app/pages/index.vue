<script setup lang="ts">
import { AlertCircle, Boxes, Database, RefreshCw, Server } from 'lucide-vue-next'

useHead({ title: 'Dashboard' })

const { user } = useAuth()
const { summary, loading, errorMessage, refresh } = useDashboard()
</script>

<template>
  <div class="grid gap-6">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-2xl font-semibold tracking-tight">
          Dashboard
        </h1>
        <p class="text-muted-foreground">
          Welcome back{{ user ? `, ${user.fullName}` : '' }}.
        </p>
      </div>
      <Button variant="outline" size="sm" :disabled="loading" @click="refresh()">
        <RefreshCw :class="{ 'animate-spin': loading }" />
        Refresh
      </Button>
    </div>

    <Alert v-if="errorMessage" variant="destructive">
      <AlertCircle />
      <AlertDescription>{{ errorMessage }}</AlertDescription>
    </Alert>

    <div class="grid gap-4 sm:grid-cols-3">
      <StatCard title="Total items" :icon="Boxes" :loading="loading" :value="summary?.totalItems" description="Rows in the items table" />
      <StatCard title="API" :icon="Server" :loading="loading" description="FastAPI backend">
        <StatusBadge v-if="summary" :status="summary.apiStatus" />
      </StatCard>
      <StatCard title="Database" :icon="Database" :loading="loading" description="PostgreSQL">
        <StatusBadge v-if="summary" :status="summary.databaseStatus" />
      </StatCard>
    </div>

    <Card>
      <CardHeader>
        <CardTitle>Items</CardTitle>
        <CardDescription>The first {{ summary?.items.length ?? 0 }} of {{ summary?.totalItems ?? 0 }} items.</CardDescription>
      </CardHeader>
      <CardContent>
        <ItemsTable :items="summary?.items ?? []" :loading="loading" />
      </CardContent>
    </Card>
  </div>
</template>
