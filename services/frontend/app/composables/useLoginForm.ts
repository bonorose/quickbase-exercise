import { z } from 'zod'
import { toast } from 'vue-sonner'
import { getApiErrorMessage, retryAfterSeconds, safeRedirectPath, statusOf } from '~/utils/apiError'

const LoginSchema = z.object({
  email: z.email('Enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
})

type LoginFields = z.infer<typeof LoginSchema>
type FieldErrors = Partial<Record<keyof LoginFields, string>>

/** Login page controller: form state, validation, submit, redirect. */
export function useLoginForm() {
  const { login } = useAuth()
  const route = useRoute()

  const fields = reactive<LoginFields>({ email: '', password: '' })
  const fieldErrors = ref<FieldErrors>({})
  const formError = ref<string | null>(null)
  const submitting = ref(false)
  const retryIn = ref(0)
  let cooldownTimer: ReturnType<typeof setInterval> | undefined

  function startCooldown(seconds: number) {
    retryIn.value = seconds
    clearInterval(cooldownTimer)
    formError.value = `Too many attempts. Try again in ${seconds} s`
    cooldownTimer = setInterval(() => {
      retryIn.value = Math.max(0, retryIn.value - 1)
      if (retryIn.value === 0) {
        clearInterval(cooldownTimer)
        formError.value = null
        return
      }
      formError.value = `Too many attempts. Try again in ${retryIn.value} s`
    }, 1000)
  }

  function validate(): LoginFields | null {
    const result = LoginSchema.safeParse(fields)
    if (result.success) {
      fieldErrors.value = {}
      return result.data
    }
    const errors: FieldErrors = {}
    for (const issue of result.error.issues) {
      const key = issue.path[0] as keyof LoginFields
      errors[key] ??= issue.message
    }
    fieldErrors.value = errors
    return null
  }

  async function submit() {
    formError.value = null
    if (retryIn.value > 0) return
    const values = validate()
    if (!values) return

    submitting.value = true
    try {
      await login(values)
      await navigateTo(safeRedirectPath(route.query.redirect), { replace: true })
    }
    catch (err) {
      if (statusOf(err) === 429) {
        const seconds = retryAfterSeconds(err)
        startCooldown(seconds)
        toast.error(formError.value ?? 'Too many attempts.')
        return
      }
      formError.value = getApiErrorMessage(err, 'Sign in failed. Please try again.')
    }
    finally {
      submitting.value = false
    }
  }

  return { fields, fieldErrors, formError, submitting, retryIn, submit }
}
