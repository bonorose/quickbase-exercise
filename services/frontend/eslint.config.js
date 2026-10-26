import pluginVue from 'eslint-plugin-vue'
import vueParser from 'vue-eslint-parser'
import tseslint from 'typescript-eslint'

export default [
  {
    files: ['app/**/*.vue'],
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        parser: tseslint.parser,
        extraFileExtensions: ['.vue'],
      },
    },
    plugins: { vue: pluginVue },
    rules: {
      'vue/no-v-html': 'error',
      'vue/multi-word-component-names': 'off',
    },
  },
]
