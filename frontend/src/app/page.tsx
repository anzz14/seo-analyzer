"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Box, CircularProgress } from "@mui/material";

import { useAuth } from "@/context/AuthContext";

export default function HomePage() {
	const auth = useAuth();
	const router = useRouter();

	useEffect(() => {
		if (!auth) {
			return;
		}

		if (auth.isLoading) {
			return;
		}

		if (auth.user) {
			router.replace("/dashboard");
		} else {
			router.replace("/login");
		}
	}, [auth, router]);

	if (!auth || auth.isLoading) {
		return (
			<Box
				sx={{
					minHeight: "100vh",
					display: "flex",
					alignItems: "center",
					justifyContent: "center",
				}}
			>
				<CircularProgress />
			</Box>
		);
	}

	return null;
}
