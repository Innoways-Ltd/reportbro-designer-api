import { createBrowserRouter } from "react-router-dom";
import Templates from "@/pages/templates";
import DefaultLayout from "@/layouts/default";

// Dynamically determine the base path from the current URL
// If URL is /ui/irmsdev2, base should be /ui/irmsdev2
// If URL is /ui or /ui/, base should be /ui
const getBasePath = (): string => {
  const pathname = window.location.pathname;
  const pathParts = pathname.split('/').filter(p => p);
  
  // Check if path starts with 'ui'
  if (pathParts.length >= 1 && pathParts[0] === 'ui') {
    // If path is exactly /ui or /ui/, use /ui as basename
    if (pathParts.length === 1 || (pathParts.length === 2 && pathParts[1] === '')) {
      return '/ui';
    }
    // If there's a second segment and it's not 'assets', it's a company-specific path
    if (pathParts.length >= 2 && pathParts[1] && pathParts[1] !== 'assets') {
      return `/ui/${pathParts[1]}`;
    }
    // Default to /ui for any other /ui/* path
    return '/ui';
  }
  return import.meta.env.VITE_PUB_PATH || '/';
};

export const router = createBrowserRouter([
  {
    path: "/",
    element: <DefaultLayout></DefaultLayout>,
    children: [
      {
        index: true,
        element: <Templates></Templates>,
      },
    ],
  },
], {
  basename: getBasePath(),
});
