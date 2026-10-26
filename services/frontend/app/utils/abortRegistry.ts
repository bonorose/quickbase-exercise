const controllers = new Set<AbortController>()

/** Track an in-flight stream so logout / user-switch can cancel it. */
export function registerAbortController(controller: AbortController): () => void {
  controllers.add(controller)
  const cleanup = () => {
    controllers.delete(controller)
  }
  controller.signal.addEventListener('abort', cleanup, { once: true })
  return cleanup
}

export function abortAllRegistered(): void {
  for (const controller of [...controllers]) {
    controller.abort()
  }
  controllers.clear()
}
