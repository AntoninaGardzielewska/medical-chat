import Link from "next/link";

export default function HomePage() {
    return (
        <main style={{ fontFamily: 'system-ui, sans-serif', padding: '2rem' }}>
            <h1>Medical Chat</h1>
            <p>
                Welcome to the Medical Chat frontend. The backend health check is available at the <code>/health</code> page.
            </p>
            <p>
                <Link href="/health">Go to Health Page</Link>
            </p>
        </main>
    );
}
