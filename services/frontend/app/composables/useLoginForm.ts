import { z } from 'zod'
import { getApiErrorMessage, safeRedirectPath } from '~/utils/apiError'

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
    const values = validate()
    if (!values) return

    submitting.value = true
    try {
      await login(values)
      await navigateTo(safeRedirectPath(route.query.redirect), { replace: true })
    }
    catch (err) {
      formError.value = getApiErrorMessage(err, 'Sign in failed. Please try again.')
    }
    finally {
      submitting.value = false
    }
  }

  return { fields, fieldErrors, formError, submitting, submit }
}
