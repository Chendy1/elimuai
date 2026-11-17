import { expect, test, type Page } from "@playwright/test";

const SESSION = {
  user: { id: "11111111-1111-1111-1111-111111111111", email: "amina@example.com", display_name: "Amina" },
  csrf_token: "csrf-test-token",
};

const json = (status: number, body: unknown) => ({
  status,
  contentType: "application/json",
  body: JSON.stringify(body),
});

async function mockSignedIn(page: Page) {
  await page.route("**/api/auth/me", (route) => route.fulfill(json(200, SESSION)));
}

test("register form blocks a short password before calling the API", async ({ page }) => {
  let called = false;
  await page.route("**/api/auth/register", (route) => {
    called = true;
    return route.abort();
  });
  await page.goto("/register");
  await page.getByLabel("Your name").fill("Amina");
  await page.getByLabel("Email").fill("amina@example.com");
  await page.getByLabel("Password").fill("short");
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page.getByText("Password must be at least 10 characters.")).toBeVisible();
  expect(called).toBe(false);
});

test("register then lands on the account page", async ({ page }) => {
  await page.route("**/api/auth/register", (route) => route.fulfill(json(201, SESSION.user)));
  await page.route("**/api/auth/login", (route) => route.fulfill(json(200, SESSION)));
  await mockSignedIn(page);
  await page.goto("/register");
  await page.getByLabel("Your name").fill("Amina");
  await page.getByLabel("Email").fill("amina@example.com");
  await page.getByLabel("Password").fill("correct-horse-battery");
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page).toHaveURL(/\/account$/);
  await expect(page.getByRole("heading", { name: "Welcome, Amina" })).toBeVisible();
});

test("login shows the server error for bad credentials", async ({ page }) => {
  await page.route("**/api/auth/login", (route) =>
    route.fulfill(json(401, { detail: "Invalid email or password." })),
  );
  await page.goto("/login");
  await page.getByLabel("Email").fill("amina@example.com");
  await page.getByLabel("Password").fill("wrong-password-123");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByText("Invalid email or password.")).toBeVisible();
});

test("login success reaches the account page, and sign out sends the CSRF token", async ({ page }) => {
  await page.route("**/api/auth/login", (route) => route.fulfill(json(200, SESSION)));
  await mockSignedIn(page);
  let csrfSent = "";
  await page.route("**/api/auth/logout", (route) => {
    csrfSent = route.request().headers()["x-csrf-token"] ?? "";
    return route.fulfill({ status: 204 });
  });
  await page.goto("/login");
  await page.getByLabel("Email").fill("amina@example.com");
  await page.getByLabel("Password").fill("correct-horse-battery");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: "Welcome, Amina" })).toBeVisible();
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page).toHaveURL(/\/login$/);
  expect(csrfSent).toBe("csrf-test-token");
});

test("account page sends signed-out visitors to sign in", async ({ page }) => {
  await page.route("**/api/auth/me", (route) => route.fulfill(json(401, { detail: "Not signed in." })));
  await page.goto("/account");
  await expect(page).toHaveURL(/\/login$/);
});

test("forgot password shows a neutral confirmation", async ({ page }) => {
  await page.route("**/api/auth/password-reset/request", (route) =>
    route.fulfill(json(202, { message: "ok" })),
  );
  await page.goto("/forgot-password");
  await page.getByLabel("Email").fill("anyone@example.com");
  await page.getByRole("button", { name: "Send reset link" }).click();
  await expect(page.getByText(/If an account exists for that email/)).toBeVisible();
});

test("reset password page without a token explains the problem", async ({ page }) => {
  await page.goto("/reset-password");
  await expect(page.getByText("This reset link is incomplete.")).toBeVisible();
});

test("reset password with a token changes the password", async ({ page }) => {
  await page.route("**/api/auth/password-reset/confirm", (route) => route.fulfill({ status: 204 }));
  await page.goto("/reset-password?token=" + "t".repeat(43));
  await page.getByLabel("New password").fill("a-brand-new-passphrase");
  await page.getByRole("button", { name: "Change password" }).click();
  await expect(page.getByText("Your password has been changed.")).toBeVisible();
});
