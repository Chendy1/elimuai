export type User = { id: string; email: string; display_name: string };
export type SessionData = { user: User; csrf_token: string };
