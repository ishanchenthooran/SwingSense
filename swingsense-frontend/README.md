# SwingSense Frontend

A modern Next.js frontend for the SwingSense AI-powered golf coaching application.

## Features

- **Home Landing Page**: Beautiful landing page with SwingSense branding and call-to-action
- **Authentication**: Supabase-powered login/signup with JWT tokens
- **Q&A Logs**: Ask golf questions and get AI-powered responses stored for future reference
- **Training Plans**: Create personalized 4-week training plans based on handicap and goals
- **Resources**: AI-curated golf resources for specific swing issues
- **Responsive Design**: Modern UI built with Tailwind CSS
- **TypeScript**: Full type safety throughout the application

## Tech Stack

- Next.js 14 (App Router)
- React 18
- TypeScript
- Tailwind CSS
- Supabase (Authentication)
- Axios (API calls)
- Lucide React (Icons)

## Getting Started

### Prerequisites

- Node.js 16+ 
- npm or yarn
- Running SwingSense backend
- Supabase project for authentication

### Installation

1. Install dependencies:
```bash
npm install
```

2. Set up environment variables:
```bash
cp env.example .env
```

Edit `.env` with your configuration:
- `REACT_APP_SUPABASE_URL`: Your Supabase project URL
- `REACT_APP_SUPABASE_ANON_KEY`: Your Supabase anonymous key
- `REACT_APP_API_URL`: Your backend API URL (default: http://localhost:8000)

3. Start the development server:
```bash
npm run dev
```

The app will be available at http://localhost:3000

## Project Structure

```
src/
├── app/                # Next.js App Router
│   ├── layout.tsx      # Root layout with providers
│   ├── page.tsx        # Home page
│   ├── globals.css     # Global styles and Tailwind imports
│   ├── login/
│   │   └── page.tsx    # Login page
│   ├── logs/
│   │   └── page.tsx    # Q&A logs page
│   ├── plans/
│   │   └── page.tsx    # Training plans page
│   └── resources/
│       └── page.tsx    # Resources page
├── components/         # Reusable UI components
│   ├── Navbar.js       # Navigation bar with auth state
│   └── ProtectedRoute.js # Route protection wrapper
├── contexts/           # React contexts
│   └── AuthContext.js  # Authentication state management
└── services/           # API services
    └── api.js          # Axios configuration and API calls
```

## API Integration

The frontend integrates with the following backend endpoints:

- **Questions**: `/questions/questions/` (GET, POST)
- **Feedback**: `/questions/feedback/` (GET)
- **Plans**: `/plans/generate` (POST), `/plans/current` (GET)
- **Resources**: `/resources/` (GET)
- **Progress**: `/progress/` (GET, POST)

## Authentication Flow

1. Users can sign up or sign in using Supabase Auth
2. JWT tokens are automatically included in API requests
3. Protected routes redirect to login if user is not authenticated
4. User state is managed globally via AuthContext

## Styling

The app uses Tailwind CSS with a custom golf-themed color palette:
- Primary green colors for golf theme
- Responsive design for mobile and desktop
- Modern card-based layouts
- Consistent spacing and typography

## Development

### Available Scripts

- `npm run dev`: Start development server
- `npm run build`: Build for production
- `npm start`: Start production server
- `npm run lint`: Run ESLint

### Code Style

- TypeScript for type safety
- Functional components with hooks
- Consistent naming conventions
- Proper error handling
- Loading states for better UX
- Next.js App Router patterns

## Deployment

1. Build the app:
```bash
npm run build
```

2. Deploy the `build` folder to your hosting service (Vercel, Netlify, etc.)

3. Make sure to set environment variables in your hosting platform

## Contributing

1. Follow the existing code style
2. Add proper error handling
3. Include loading states
4. Test on different screen sizes
5. Update documentation as needed
