import { Roboto } from "next/font/google";

import AppProviders from "@/components/providers/AppProviders";

const roboto = Roboto({
	subsets: ["latin"],
	weight: ["300", "400", "500", "700"],
});

export default function RootLayout({
	children,
}: Readonly<{
	children: React.ReactNode;
}>) {
	return (
		<html lang="en">
			<body className={roboto.className}>
				<AppProviders>{children}</AppProviders>
			</body>
		</html>
	);
}
