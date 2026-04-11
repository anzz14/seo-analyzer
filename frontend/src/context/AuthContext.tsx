"use client";

import {
	createContext,
	useCallback,
	useContext,
	useEffect,
	useMemo,
	useState,
	type ReactNode,
} from "react";
import { useRouter } from "next/navigation";

import api, { setAuthToken } from "@/lib/api";
import type { AuthUser, TokenResponse } from "@/types/auth";

interface AuthContextType {
	user: AuthUser | null;
	isLoading: boolean;
	login: (email: string, password: string) => Promise<void>;
	logout: () => void;
	register: (email: string, password: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function decodeTokenPayload(token: string): AuthUser | null {
	try {
		const parts = token.split(".");
		if (parts.length < 2) {
			return null;
		}

		const base64Url = parts[1];
		const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
		const padLen = (4 - (base64.length % 4)) % 4;
		const padded = base64 + "=".repeat(padLen);
		const json = atob(padded);
		const payload = JSON.parse(json) as { sub?: string; email?: string };

		if (!payload.sub || !payload.email) {
			return null;
		}

		return { user_id: payload.sub, email: payload.email };
	} catch {
		return null;
	}
}

export function AuthProvider({ children }: { children: ReactNode }) {
	const router = useRouter();
	const [user, setUser] = useState<AuthUser | null>(null);
	const [isLoading, setIsLoading] = useState(true);

	useEffect(() => {
		const token = localStorage.getItem("seo_jwt");

		if (token) {
			setAuthToken(token);
			const decodedUser = decodeTokenPayload(token);
			if (decodedUser) {
				setUser(decodedUser);
			} else {
				setAuthToken(null);
				localStorage.removeItem("seo_jwt");
			}
		}

		setIsLoading(false);
	}, []);

	const login = useCallback(async (email: string, password: string): Promise<void> => {
		const { data } = await api.post<TokenResponse>("/auth/login", { email, password });

		setAuthToken(data.access_token);
		localStorage.setItem("seo_jwt", data.access_token);
		setUser({ user_id: data.user_id, email: data.email });
		router.push("/dashboard");
	}, [router]);

	const logout = useCallback((): void => {
		setAuthToken(null);
		localStorage.removeItem("seo_jwt");
		setUser(null);
		router.push("/login");
	}, [router]);

	const register = useCallback(async (email: string, password: string): Promise<void> => {
		await api.post<TokenResponse>("/auth/register", { email, password });
		await login(email, password);
	}, [login]);

	const value = useMemo<AuthContextType>(
		() => ({
			user,
			isLoading,
			login,
			logout,
			register,
		}),
		[user, isLoading, login, logout, register],
	);

	return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
