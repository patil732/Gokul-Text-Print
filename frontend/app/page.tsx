import { redirect } from "next/navigation";

/**
 * Root page — immediately redirects to the dashboard.
 * In Sprint 7 the dashboard/page.tsx is the smoke-test entry point.
 */
export default function Home() {
  redirect("/dashboard");
}
