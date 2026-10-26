import { getApiErrorMessage, isNotFound } from '~/utils/apiError'
import { useToast } from '~/composables/useToast'

export default defineNuxtPlugin((nuxtApp) => {
  const { error } = useToast()

  nuxtApp.vueApp.config.errorHandler = (err) => {
    if (isNotFound(err)) return
    error(getApiErrorMessage(err, 'Something went wrong'))
  }

  if (typeof window === 'undefined') return
  window.addEventListener('unhandledrejection', (event) => {
    if (isNotFound(event.reason)) return
    error(getApiErrorMessage(event.reason, 'Something went wrong'))
  })
})
