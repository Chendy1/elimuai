export type User = { id: string; email: string; display_name: string };
export type SessionData = { user: User; csrf_token: string };
export type Learner = { id: string; nickname: string; grade: number };
export type ConsentNotice = { version: string; title: string; text: string; is_draft: boolean };
