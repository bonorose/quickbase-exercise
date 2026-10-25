<script setup lang="ts">
import type { ItemSummary } from '~/types/models'

defineProps<{
  items: ItemSummary[]
  loading?: boolean
}>()

const dateFormat = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' })
</script>

<template>
  <Table>
    <TableHeader>
      <TableRow>
        <TableHead class="w-16">
          ID
        </TableHead>
        <TableHead>Name</TableHead>
        <TableHead>Description</TableHead>
        <TableHead class="text-right">
          Created
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
      <TableRow v-else-if="items.length === 0">
        <TableCell colspan="4" class="h-24 text-center text-muted-foreground">
          No items yet.
        </TableCell>
      </TableRow>
      <TableRow v-for="item in items" v-else :key="item.id">
        <TableCell class="font-mono text-muted-foreground">
          {{ item.id }}
        </TableCell>
        <TableCell class="font-medium">
          {{ item.name }}
        </TableCell>
        <TableCell class="text-muted-foreground">
          {{ item.description }}
        </TableCell>
        <TableCell class="text-right text-muted-foreground">
          {{ dateFormat.format(item.createdAt) }}
        </TableCell>
      </TableRow>
    </TableBody>
  </Table>
</template>
