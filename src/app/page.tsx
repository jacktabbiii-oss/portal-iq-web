import { redirect } from "next/navigation";

export default function HomePage() {
  // Redirect to dashboard (auth provider will handle redirect to login if not authenticated)
  redirect("/dashboard");
}
