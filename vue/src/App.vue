<template>
  <AppLayout>
    <router-view v-slot="{ Component }">
      <transition name="page-fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </AppLayout>
  <ToastHost />
</template>

<script setup>
import AppLayout from './components/AppLayout.vue'
import ToastHost from './components/ToastHost.vue'
</script>
