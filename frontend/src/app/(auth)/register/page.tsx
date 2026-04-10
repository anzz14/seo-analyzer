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

export default function RegisterPage() {
	const auth = useAuth();
	const [email, setEmail] = useState("");
	const [password, setPassword] = useState("");
	const [confirmPassword, setConfirmPassword] = useState("");
	const [error, setError] = useState<string | null>(null);
	const [isLoading, setIsLoading] = useState(false);

	const handleRegister = async () => {
		if (!auth) {
			return;
		}

		setError(null);

		if (password.length < 8) {
			setError("Password must be at least 8 characters.");
			return;
		}

		if (password !== confirmPassword) {
			setError("Passwords do not match.");
			return;
		}

		setIsLoading(true);
		try {
			await auth.register(email, password);
		} catch {
			setError("Unable to create account. Please try again.");
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
						<Typography variant="h5">Create Account</Typography>

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

						<TextField
							type="password"
							label="Confirm Password"
							fullWidth
							value={confirmPassword}
							onChange={(event) => setConfirmPassword(event.target.value)}
						/>

						<Button
							variant="contained"
							fullWidth
							onClick={handleRegister}
							disabled={isLoading}
						>
							{isLoading ? <CircularProgress size={20} color="inherit" /> : "Create Account"}
						</Button>

						<Typography variant="body2">
							Already have an account? <Link href="/login">Sign in</Link>
						</Typography>
					</Stack>
				</CardContent>
			</Card>
		</Box>
	);
}
