export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Auth pages have their own layout (no sidebar)
  return <>{children}</>;
}
