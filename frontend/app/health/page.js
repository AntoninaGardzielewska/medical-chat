import Link from "next/link";

async function getHealthStatus() {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const response = await fetch(`${apiUrl}/health`, { cache: "no-store" });

    if (!response.ok) {
        throw new Error(`Health request failed: ${response.status}`);
    }

    return response.json();
}

export default async function HealthPage() {
    let health;
    let error = null;

    try {
        health = await getHealthStatus();
    } catch (err) {
        error = err instanceof Error ? err.message : String(err);
    }

    return (
        <main style={{ fontFamily: 'system-ui, sans-serif', padding: '2rem' }}>
            <h1>Health Page</h1>
            {error ? (
                <div>
                    <p style={{ color: 'red' }}>Unable to load health status.</p>
                    <pre>{error}</pre>
                </div>
            ) : (
                <div>
                    <p>Status: <strong>{health.status}</strong></p>
                    <p>Version: <strong>{health.version}</strong></p>
                </div>
            )}
            <p>
                <Link href="/">Back to Home</Link>
            </p>
        </main>
    );
}
