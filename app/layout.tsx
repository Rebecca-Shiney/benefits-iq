import type { Metadata } from "next";
import "./globals.css";
import "@copilotkit/react-ui/styles.css";
import "./dashboard.css";

export const metadata: Metadata = {
  title: "Benefits IQ | Human-led benefits review",
  description: "Synthetic special authorization and Member 360 workspace",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
