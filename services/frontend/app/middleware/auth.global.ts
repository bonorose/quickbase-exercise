/**
 * Runs on every navigation. Every page requires a signed-in user unless it is explicitly
 * marked `definePageMeta({ public: true })` - currently only /login.
 * Public pages are for signed-out users, so an authenticated visitor is sent home.
 */
export default defineNuxtRouteMiddleware(async (to) => {
  const { restoreSession } = useAuth()
  const authenticated = await restoreSession()

  if (to.meta.public) {
    return authenticated ? navigateTo('/') : undefined
  }

  if (!authenticated) {
    return navigateTo({ path: '/login', query: { redirect: to.fullPath } })
  }
})
