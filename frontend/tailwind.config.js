/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: {
                    DEFAULT: '#2563eb',
                    dark: '#1d4ed8',
                },
                secondary: '#059669',
                accent: '#dc2626',
                background: '#fafafa',
                surface: '#ffffff',
                text: {
                    primary: '#1f2937',
                    secondary: '#6b7280',
                },
                border: '#e5e7eb',
                success: '#10b981',
                warning: '#f59e0b',
                error: '#ef4444',
                info: '#3b82f6',
            },
            fontFamily: {
                medical: ['Inter', 'Helvetica Neue', 'sans-serif'],
            },
        },
    },
    plugins: [
        require('@tailwindcss/typography'),
    ],
}
