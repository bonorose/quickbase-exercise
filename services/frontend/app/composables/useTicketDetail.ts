import { getApiErrorMessage, isNotFound } from '~/utils/apiError'

export function useTicketDetail(id: MaybeRefOrGetter<number | null>) {
  const { tickets } = useServices()
  const ticketId = computed(() => toValue(id))

  const { data, status, error, refresh } = useAsyncData(
    () => `tickets:detail:${ticketId.value ?? 'none'}`,
    async () => {
      if (ticketId.value == null) return null
      return tickets.get(ticketId.value)
    },
    { watch: [ticketId], dedupe: 'cancel' },
  )

  return {
    ticket: computed(() => data.value ?? null),
    loading: computed(() => ticketId.value != null && status.value === 'pending'),
    notFound: computed(() => !!error.value && isNotFound(error.value)),
    errorMessage: computed(() => {
      if (!error.value || isNotFound(error.value)) return null
      return getApiErrorMessage(error.value, 'Could not load that ticket.')
    }),
    refresh,
  }
}
