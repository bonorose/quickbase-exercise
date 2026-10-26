<script setup lang="ts">
import { AlertCircle, CircleDashed, Database, RefreshCw, Server, ShieldAlert } from 'lucide-vue-next'
import { formatRelativeTime } from '~/utils/relativeTime'

useHead({ title: 'Dashboard' })

const { user } = useAuth()
const { summary, loading, errorMessage, refresh } = useDashboard()
</script>

<template>
  <div class="grid gap-6">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-3xl font-extrabold tracking-tight text-forest">
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

    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <StatCard title="Open" :icon="CircleDashed" :loading="loading" :value="summary?.openCount" description="Tickets waiting on the team" />
      <StatCard title="Blocked" :icon="ShieldAlert" :loading="loading" :value="summary?.blockedCount" description="Waiting on someone else" />
      <StatCard title="Closed" :icon="CircleDashed" :loading="loading" :value="summary?.closedCount" description="Resolved tickets" />
    </div>

    <Card>
      <CardHeader>
        <CardTitle>Recently updated</CardTitle>
        <CardDescription>The five newest updates in your team.</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead class="w-20">
                ID
              </TableHead>
              <TableHead>Title</TableHead>
              <TableHead>Status</TableHead>
              <TableHead class="text-right">
                Updated
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <template v-if="loading">
              <TableRow v-for="n in 3" :key="n">
                <TableCell v-for="c in 4" :key="c">
                  <Skeleton class="h-4 w-full" />
                </TableCell>
              </TableRow>
            </template>
            <TableRow v-else-if="!summary?.recent.length">
              <TableCell colspan="4" class="h-24 text-center text-muted-foreground">
                No tickets yet.
              </TableCell>
            </TableRow>
            <TableRow v-for="row in summary?.recent ?? []" v-else :key="row.id">
              <TableCell class="font-mono text-xs text-muted-foreground">
                <NuxtLink :to="`/tickets?id=${row.id}`" class="text-forest underline decoration-teal-signal underline-offset-4 hover:decoration-2">
                  {{ row.id }}
                </NuxtLink>
              </TableCell>
              <TableCell class="font-medium">
                <NuxtLink :to="`/tickets?id=${row.id}`" class="text-forest underline decoration-teal-signal underline-offset-4 hover:decoration-2">
                  {{ row.title }}
                </NuxtLink>
              </TableCell>
              <TableCell>
                <StatusBadge :status="row.status" />
              </TableCell>
              <TableCell class="text-right font-mono text-xs text-muted-foreground">
                {{ formatRelativeTime(row.updatedAt) }}
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  </div>
</template>
