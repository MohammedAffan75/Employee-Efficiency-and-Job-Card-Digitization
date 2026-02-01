# Frontend

React + TypeScript + Vite frontend for the Employee Efficiency Management System.

## Setup

### Install Dependencies
```bash
npm install
```

### Run Development Server
```bash
npm run dev
```

The application will be available at http://localhost:5173

## Build for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Preview Production Build

```bash
npm run preview
```

## Technologies

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **TailwindCSS** - Styling
- **React Router** - Routing
- **Axios** - HTTP client
- **Lucide React** - Icons

## Project Structure

- `src/main.tsx` - Application entry point
- `src/App.tsx` - Root component with routing
- `src/index.css` - Global styles and TailwindCSS imports
- `src/context/` - React context providers
- `src/components/` - Reusable components
- `src/pages/` - Page components
- `public/` - Static assets

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Environment Variables

Create `.env.local` file:
```env
VITE_API_URL=http://localhost:8000
```
