"use client";

import { useState } from "react";
import Link from "next/link";
import {
	Alert,
	Box,
	Button,
	Card,
	CardContent,
	CircularProgress,
	Stack,
	TextField,
	Typography,
} from "@mui/material";

import { useAuth } from "@/context/AuthContext";

export default function LoginPage() {
	const auth = useAuth();
	const [email, setEmail] = useState("");
	const [password, setPassword] = useState("");
	const [error, setError] = useState<string | null>(null);
	const [isLoading, setIsLoading] = useState(false);

	const handleSignIn = async () => {
		if (!auth) {
			return;
		}

		setError(null);
		setIsLoading(true);

		try {
			await auth.login(email, password);
		} catch {
			setError("Invalid email or password.");
		} finally {
			setIsLoading(false);
		}
	};

	return (
		<Box
			sx={{
				minHeight: "100vh",
				display: "flex",
				alignItems: "center",
				justifyContent: "center",
				px: 2,
			}}
		>
			<Card sx={{ width: "100%", maxWidth: 400 }}>
				<CardContent>
					<Stack spacing={2.5}>
						<Typography variant="h5">Sign In</Typography>

						{error ? <Alert severity="error">{error}</Alert> : null}

						<TextField
							type="email"
							label="Email"
							fullWidth
							value={email}
							onChange={(event) => setEmail(event.target.value)}
						/>

						<TextField
							type="password"
							label="Password"
							fullWidth
							value={password}
							onChange={(event) => setPassword(event.target.value)}
						/>

						<Button
							variant="contained"
							fullWidth
							onClick={handleSignIn}
							disabled={isLoading}
						>
							{isLoading ? <CircularProgress size={20} color="inherit" /> : "Sign In"}
						</Button>

						<Typography variant="body2">
							Don&apos;t have an account? <Link href="/register">Register</Link>
						</Typography>
					</Stack>
				</CardContent>
			</Card>
		</Box>
	);
}
