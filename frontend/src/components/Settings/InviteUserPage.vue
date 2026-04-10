<template>
  <div class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8">
    <h2 class="text-xl font-semibold">{{ __('Invite users') }}</h2>
    <p class="text-p-base text-ink-gray-6 max-w-xl">
      {{
        __(
          'Havano CRM does not use the CRM Invitation DocType. Add or invite users from Desk → User (or User Invitation) with Sales User / Sales Manager roles.',
        )
      }}
    </p>
  </div>
</template>
<script setup></script>
