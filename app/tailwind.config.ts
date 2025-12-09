import type { Config } from "tailwindcss";

export default {
    content: [
        "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: {
                    50: 'hsl(260, 100%, 97%)',
                    100: 'hsl(260, 100%, 94%)',
                    200: 'hsl(260, 100%, 88%)',
                    300: 'hsl(260, 100%, 80%)',
                    400: 'hsl(260, 100%, 70%)',
                    500: 'hsl(260, 100%, 60%)',
                    600: 'hsl(260, 90%, 50%)',
                    700: 'hsl(260, 80%, 40%)',
                    800: 'hsl(260, 70%, 30%)',
                    900: 'hsl(260, 60%, 20%)',
                },
                accent: {
                    50: 'hsl(340, 100%, 97%)',
                    100: 'hsl(340, 100%, 94%)',
                    200: 'hsl(340, 100%, 88%)',
                    300: 'hsl(340, 100%, 80%)',
                    400: 'hsl(340, 100%, 70%)',
                    500: 'hsl(340, 100%, 60%)',
                    600: 'hsl(340, 90%, 50%)',
                    700: 'hsl(340, 80%, 40%)',
                },
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
            },
            animation: {
                'float': 'float 6s ease-in-out infinite',
                'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                'shimmer': 'shimmer 2s linear infinite',
            },
            keyframes: {
                float: {
                    '0%, 100%': { transform: 'translateY(0px)' },
                    '50%': { transform: 'translateY(-20px)' },
                },
                shimmer: {
                    '0%': { backgroundPosition: '-200% 0' },
                    '100%': { backgroundPosition: '200% 0' },
                },
            },
        },
    },
    plugins: [],
} satisfies Config;
