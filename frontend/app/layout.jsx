export const metadata = {
  title: "Medical Chat",
  description: "AI-powered medical chat assistant",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
