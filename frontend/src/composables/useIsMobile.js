import { ref, onMounted, onUnmounted } from 'vue'

const BREAKPOINT = 768

export function useIsMobile() {
  const isMobile = ref(window.innerWidth <= BREAKPOINT)

  function onResize() {
    isMobile.value = window.innerWidth <= BREAKPOINT
  }

  onMounted(() => window.addEventListener('resize', onResize))
  onUnmounted(() => window.removeEventListener('resize', onResize))

  return { isMobile }
}
