export default function OIDCProtectedRoute({ children }: { children: React.ReactNode }) {
  // No authentication required - direct access
  return <>{children}</>;
}
