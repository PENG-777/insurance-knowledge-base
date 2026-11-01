import { reactive } from 'vue'

const state = reactive({ items: [] })
let seq = 0

export function toast(message, type = 'success', duration = 3200) {
  const id = ++seq
  state.items.push({ id, message, type })
  window.setTimeout(() => {
    const index = state.items.findIndex((item) => item.id === id)
    if (index > -1) state.items.splice(index, 1)
  }, duration)
}

export function useToast() {
  return { toasts: state.items, toast }
}
