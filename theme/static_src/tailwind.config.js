/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['../../templates/**/*.html', '../../**/templates/**/*.html', '../../**/*.py'],
  theme: {
    extend: {
      colors: {
        primary: '#174443',
        secondary: '#e7aa4e',
      },
    },
  },
  plugins: [],
};
