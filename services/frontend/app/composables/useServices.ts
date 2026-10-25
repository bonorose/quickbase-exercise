/** Typed access to the services wired in plugins/services.ts */
export function useServices() {
  return useNuxtApp().$services
}
