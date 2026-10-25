import { getApiErrorMessage } from '~/utils/apiError'

/** Dashboard page controller: loads the summary and exposes view state. */
export function useDashboard() {
  const { dashboard } = useServices()

  const { data: summary, status, error, refresh } = useAsyncData(
    'dashboard-summary',
    () => dashboard.getSummary(),
  )

  return {
    summary,
    loading: computed(() => status.value === 'pending'),
    errorMessage: computed(() => error.value ? getApiErrorMessage(error.value, 'Could not load the dashboard.') : null),
    refresh,
  }
}
