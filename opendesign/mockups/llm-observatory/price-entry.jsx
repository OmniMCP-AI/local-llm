import React from "react";
import { createRoot } from "react-dom/client";
import { LocaleProvider } from "./locale";
import { HostedPrices } from "./price-comparison";

createRoot(document.getElementById("root")).render(<LocaleProvider><HostedPrices /></LocaleProvider>);
