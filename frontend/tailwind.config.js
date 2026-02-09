/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: "#2563eb",
                "primary-hover": "#1d4ed8",
                "bg-dark": "#0f172a",
                "card-dark": "#1e293b",
                "text-main": "#f8fafc",
                "text-muted": "#94a3b8",
                accent: "#38bdf8",
            },
            fontFamily: {
                sans: ['Inter', 'sans-serif'],
                outfit: ['Outfit', 'sans-serif'],
            },
        },
    },
    plugins: [],
}
