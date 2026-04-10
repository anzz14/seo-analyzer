export interface TokenResponse {
	access_token: string;
	token_type: string;
	user_id: string;
	email: string;
}

export interface AuthUser {
	user_id: string;
	email: string;
}
