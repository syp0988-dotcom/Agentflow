<template>
  <div class="flex items-start gap-3 animate-fade-in">
    <div
      class="w-6 h-6 rounded-md bg-primary/20 flex items-center justify-center text-[10px] font-bold flex-shrink-0"
    >
      OF
    </div>
    <div class="flex items-center gap-1.5 py-2">
      <span
        v-for="i in 3"
        :key="i"
        class="thinking-dot w-2 h-2 rounded-full bg-primary/60 inline-block"
      ></span>
    </div>
  </div>
</template>
