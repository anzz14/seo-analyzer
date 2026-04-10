import axios from "axios";

const api = axios.create({
	baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1",
});

export let authToken: string | null = null;

export function setAuthToken(token: string | null): void {
	authToken = token;
}

api.interceptors.request.use((config) => {
	if (!authToken && typeof window !== "undefined") {
		authToken = localStorage.getItem("seo_jwt");
	}

	if (authToken) {
		config.headers = config.headers ?? {};
		if (typeof config.headers.set === "function") {
			config.headers.set("Authorization", `Bearer ${authToken}`);
		} else {
			(config.headers as Record<string, string>).Authorization = `Bearer ${authToken}`;
		}
	}

	return config;
});

api.interceptors.response.use(
	(response) => response,
	(error) => {
		if (error?.response?.status === 401 || error?.response?.status === 403) {
			authToken = null;
			if (typeof window !== "undefined") {
				localStorage.removeItem("seo_jwt");
			}
			if (typeof window !== "undefined") {
				window.location.href = "/login";
			}
		}
		return Promise.reject(error);
	},
);

export default api;
