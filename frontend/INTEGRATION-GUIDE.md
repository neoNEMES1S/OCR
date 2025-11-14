# BackgroundPaths Component Integration Guide

## ✅ Setup Complete!

The BackgroundPaths component has been integrated into your OCR PDF Search System.

## 🎨 What Was Added

### 1. **Tailwind CSS Setup**
- ✅ `tailwind.config.js` - Tailwind configuration with shadcn/ui theme
- ✅ `postcss.config.js` - PostCSS configuration
- ✅ `src/index.css` - Tailwind directives and CSS variables
- ✅ Updated `vite.config.ts` with path aliases

### 2. **shadcn/ui Structure**
- ✅ `src/lib/utils.ts` - cn() utility for class merging
- ✅ `src/components/ui/` - UI components directory
- ✅ `src/components/ui/button.tsx` - Button component
- ✅ `src/components/ui/background-paths.tsx` - BackgroundPaths component

### 3. **New Home Page**
- ✅ `src/pages/HomePage.tsx` - Landing page with BackgroundPaths
- ✅ Updated App.tsx with Tailwind classes and new route
- ✅ Updated navigation to include Home link

### 4. **Dependencies Added**

```json
{
  "dependencies": {
    "@radix-ui/react-slot": "^1.0.2",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.0.0",
    "framer-motion": "^10.16.16",
    "tailwind-merge": "^2.2.0"
  },
  "devDependencies": {
    "@types/node": "^20.10.6",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32",
    "tailwindcss": "^3.4.0",
    "tailwindcss-animate": "^1.0.7"
  }
}
```

## 🚀 Installation Steps

Run these commands in your terminal:

```bash
cd frontend

# Install all new dependencies
npm install

# Start dev server
npm run dev
```

## 📁 File Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/                    # shadcn/ui components (NEW)
│   │   │   ├── button.tsx
│   │   │   └── background-paths.tsx
│   │   ├── FolderSettings.tsx
│   │   ├── FolderStatus.tsx
│   │   ├── SearchBar.tsx
│   │   └── SearchResults.tsx
│   ├── lib/                       # Utilities (NEW)
│   │   └── utils.ts
│   ├── pages/
│   │   ├── HomePage.tsx           # NEW - Landing page
│   │   ├── SearchPage.tsx
│   │   └── SettingsPage.tsx
│   ├── App.tsx                    # Updated with Tailwind
│   ├── main.tsx
│   ├── index.css                  # NEW - Tailwind directives
│   └── api.ts
├── tailwind.config.js             # NEW
├── postcss.config.js              # NEW
├── vite.config.ts                 # Updated
├── tsconfig.json                  # Updated
└── package.json                   # Updated
```

## 🎯 How It Works

### Routes
- **`/`** - Beautiful landing page with BackgroundPaths component
- **`/search`** - Search functionality (previously at /)
- **`/settings`** - Settings page

### BackgroundPaths Component

**Props:**
- `title` (optional) - Text to display (default: "Background Paths")
- `onButtonClick` (optional) - Button click handler

**Features:**
- Animated floating paths background
- Letter-by-letter animation for title
- Beautiful gradient button with hover effects
- Dark mode support
- Fully responsive

**Usage Example:**
```tsx
import { BackgroundPaths } from '@/components/ui/background-paths';

function MyPage() {
  return (
    <BackgroundPaths 
      title="My Custom Title"
      onButtonClick={() => console.log('Clicked!')}
    />
  );
}
```

## 🎨 Customization

### Change Title
Edit `src/pages/HomePage.tsx`:
```tsx
<BackgroundPaths title="Your Custom Title" />
```

### Change Button Text
Edit `src/components/ui/background-paths.tsx`:
```tsx
<span className="opacity-90 group-hover:opacity-100 transition-opacity">
  Your Button Text
</span>
```

### Add More UI Components

To add more shadcn/ui components:

```bash
# Example: Add a card component
npx shadcn-ui@latest add card

# Add dialog
npx shadcn-ui@latest add dialog

# Add dropdown menu
npx shadcn-ui@latest add dropdown-menu
```

All components will be added to `src/components/ui/`

## 🌈 Tailwind Classes

You can now use Tailwind CSS throughout your app:

```tsx
// Before (inline styles)
<div style={{ padding: '20px', backgroundColor: '#f5f5f5' }}>

// After (Tailwind)
<div className="p-5 bg-gray-100">
```

## 🎭 Dark Mode

Dark mode is already configured! Toggle it with:

```tsx
// Add dark mode toggle button
<button onClick={() => document.documentElement.classList.toggle('dark')}>
  Toggle Dark Mode
</button>
```

## 📖 Resources

- **Tailwind CSS Docs**: https://tailwindcss.com/docs
- **shadcn/ui Docs**: https://ui.shadcn.com
- **Framer Motion Docs**: https://www.framer.com/motion

## 🐛 Troubleshooting

### "Cannot find module '@/components/ui/button'"
Run: `npm install` to ensure all dependencies are installed

### Tailwind classes not working
1. Check `index.css` is imported in `main.tsx`
2. Restart dev server: `npm run dev`

### Path alias not working
Check `tsconfig.json` and `vite.config.ts` have the @ alias configured

## ✨ Next Steps

1. **Install dependencies**: `npm install`
2. **Start dev server**: `npm run dev`
3. **Visit**: http://localhost:3000
4. **See the beautiful landing page!**

## 🎨 Migrate Existing Components

You can now migrate your existing components to use Tailwind:

**FolderSettings.tsx** - Replace inline styles with Tailwind classes
**SearchBar.tsx** - Use Tailwind utilities
**SearchResults.tsx** - Style with Tailwind

Example migration:
```tsx
// Before
<button style={{ padding: '10px 20px', backgroundColor: '#007bff' }}>

// After
<button className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700">
```

Enjoy your beautiful new landing page! 🚀

