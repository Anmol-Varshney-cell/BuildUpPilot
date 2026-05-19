export function notFound(_req, res) {
    res.status(404).json({ message: "Route not found" });
}
export function errorHandler(err, _req, res, _next) {
    console.error(err);
    const message = err instanceof Error ? err.message : "Internal server error";
    res.status(500).json({ message: "Internal server error", error: message });
}
