import { getApiErrorMessage } from '~/utils/apiError'
import { registerAbortController } from '~/utils/abortRegistry'

/**
 * Reusable streaming state for any LLM-backed feature: accumulates deltas into `text`,
 * exposes the transient `status` line, the final `model`, and a user-facing `error`.
 * Starting a new stream (or unmounting the component) aborts the previous one.
 */
export function useLLMStream() {
  const { llm } = useServices()

  const text = ref('')
  const status = ref<string | null>(null)
  const model = ref<string | null>(null)
  const error = ref<string | null>(null)
  const streaming = ref(false)
  let controller: AbortController | null = null

  function stop() {
    controller?.abort()
    controller = null
  }

  function reset() {
    stop()
    text.value = ''
    status.value = null
    model.value = null
    error.value = null
  }

  async function start(prompt: string) {
    reset()
    const current = new AbortController()
    registerAbortController(current)
    controller = current
    streaming.value = true
    try {
      for await (const event of llm.streamCompletion(prompt, current.signal)) {
        // A status line lasts until anything else arrives
        status.value = event.type === 'status' ? event.message : null
        switch (event.type) {
          case 'delta':
            text.value += event.text
            break
          case 'done':
            model.value = event.model
            break
          case 'error':
            error.value = event.message
            break
        }
      }
    }
    catch (err) {
      if (!current.signal.aborted) {
        error.value = getApiErrorMessage(err, 'The response could not be generated.')
      }
    }
    finally {
      if (controller === current) controller = null
      // Skip only when a newer start() has already taken over
      if (controller === null) {
        streaming.value = false
        status.value = null
      }
    }
  }

  if (getCurrentScope()) onScopeDispose(stop)

  return {
    text: readonly(text),
    status: readonly(status),
    model: readonly(model),
    error: readonly(error),
    streaming: readonly(streaming),
    start,
    stop,
    reset,
  }
}
