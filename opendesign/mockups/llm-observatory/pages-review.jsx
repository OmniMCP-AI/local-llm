import React from "react";
import { createRoot } from "react-dom/client";
import { Highlights } from "./highlights";

const fallback = document.querySelector("[data-home-highlights]:not([hidden])");
if (fallback) {
  const root = document.createElement("div");
  root.className = "pages-review-highlights";
  fallback.before(root);
  createRoot(root).render(<Highlights />);
}
