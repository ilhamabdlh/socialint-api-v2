# Environment Variables Setup

## 📋 Overview

Aplikasi ini menggunakan environment variables untuk mengkonfigurasi API URL. Ini memungkinkan Anda untuk dengan mudah switch antara localhost, staging, dan production API tanpa perlu mengubah kode.

## 🚀 Quick Start

### 1. Buat File `.env.local`

Buat file `.env.local` di root folder `teorema-social-intelligence/` dengan konten berikut:

```env
# API Configuration
VITE_API_URL=http://localhost:8000
VITE_API_PREFIX=/api/v1
```

### 2. Restart Dev Server

Setelah membuat atau mengubah file `.env.local`, restart dev server:

```bash
npm run dev
```

## 📝 Environment Variables

### Required Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `VITE_API_URL` | Base URL untuk API backend | `http://localhost:8000` | `https://api.teoremaintelligence.com` |
| `VITE_API_PREFIX` | API prefix path | `/api/v1` | `/api/v1` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_APP_NAME` | Nama aplikasi | `Social Intelligence Dashboard` |
| `VITE_APP_VERSION` | Versi aplikasi | `2.1.0` |

## 🔧 Environment Configurations

### Development (Localhost)

```env
VITE_API_URL=http://localhost:8000
VITE_API_PREFIX=/api/v1
```

### Staging

```env
VITE_API_URL=https://api.staging.teoremaintelligence.com
VITE_API_PREFIX=/api/v1
```

### Production

```env
VITE_API_URL=https://api.teoremaintelligence.com
VITE_API_PREFIX=/api/v1
```

## 📁 File Priority

Vite akan membaca environment variables dengan urutan prioritas berikut:

1. `.env.production.local` (hanya untuk production build)
2. `.env.local` (local development, diabaikan oleh git)
3. `.env.production` (hanya untuk production build)
4. `.env` (default, bisa di-commit)

## ⚠️ Important Notes

1. **File `.env.local` tidak akan di-commit ke git** (sudah ada di `.gitignore`)
2. **Environment variables harus prefix dengan `VITE_`** untuk bisa diakses di frontend
3. **Restart dev server** setelah mengubah environment variables
4. **Variables di-inject pada build time**, bukan runtime

## 🧪 Testing

### Test dengan Localhost

1. Set `VITE_API_URL=http://localhost:8000` di `.env.local`
2. Pastikan backend berjalan di `http://localhost:8000`
3. Restart dev server
4. Check Network tab di browser - semua API calls harus ke `http://localhost:8000`

### Test dengan Staging

1. Set `VITE_API_URL=https://api.staging.teoremaintelligence.com` di `.env.local`
2. Restart dev server
3. Check Network tab - semua API calls harus ke staging URL

## 🔍 Verifikasi

Setelah setup, Anda bisa verifikasi di browser console:

```javascript
console.log('API Config:', import.meta.env.VITE_API_URL);
```

Atau di Network tab, pastikan semua API requests menggunakan URL dari environment variable.

## 📚 References

- [Vite Environment Variables](https://vitejs.dev/guide/env-and-mode.html)
- [Vite Environment Variables Best Practices](https://vitejs.dev/guide/env-and-mode.html#env-files)

