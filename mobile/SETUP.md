# Mobile — Quick Start

## Prerequisites
- Node.js 22 (via nvm)
- Expo Go installed on your phone (or an Android/iOS simulator)

## First run

```bash
# 1. Install dependencies
npm install

# 2. Start the dev server
npm start

# 3. Scan the QR code with Expo Go, or press 'a' for Android / 'i' for iOS
```

## Current screens
| Route | Screen |
|-------|--------|
| `/(auth)/index` | Welcome / Landing screen ← **start here** |
| `/(auth)/sign-in` | Sign In (placeholder) |
| `/(auth)/sign-up` | Sign Up (placeholder) |
| `/(tabs)/index` | Home Feed (placeholder) |
| `/(tabs)/bars` | Bar Catalog (placeholder) |
| `/(tabs)/friends` | Friends (placeholder) |
| `/(tabs)/profile` | Profile (placeholder) |

## Stack
- **Expo SDK 52** + **Expo Router 4** (file-based routing)
- **Tamagui** — component library & theming (`theme/tamagui.config.ts`)
- **Redux Toolkit** — client state (`store/index.ts`)
- **Fonts** — Fraunces · Plus Jakarta Sans · JetBrains Mono (via `@expo-google-fonts`)
