/** Client-side checks that mirror the server's rules. The server remains the authority. */
export function validateName(value: string): string | null {
  const v = value.trim();
  if (v.length === 0) return "Please enter your name.";
  if (v.length > 100) return "Name must be 100 characters or fewer.";
  return null;
}

export function validateEmail(value: string): string | null {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim()) ? null : "Please enter a valid email address.";
}

export function validatePassword(password: string, email?: string): string | null {
  if (password.length < 10) return "Password must be at least 10 characters.";
  if (password.length > 128) return "Password must be 128 characters or fewer.";
  if (email && password.toLowerCase() === email.trim().toLowerCase()) {
    return "Password must not be the same as your email address.";
  }
  return null;
}

export function validateNickname(value: string): string | null {
  const v = value.trim();
  if (v.length < 1 || v.length > 50) return "Nickname must be 1 to 50 characters.";
  if (v.includes("@") || /\d{6,}/.test(v)) {
    return "Please use a nickname only: no email addresses or phone numbers.";
  }
  return null;
}
