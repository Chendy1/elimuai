import { expect, test, type Page } from "@playwright/test";

type L = { id: string; nickname: string; grade: number };

const SESSION = {
  user: { id: "11111111-1111-1111-1111-111111111111", email: "amina@example.com", display_name: "Amina" },
  csrf_token: "csrf-test-token",
};
const NOTICE = {
  version: "0.1-draft",
  title: "Consent to create a learner profile (DRAFT)",
  text: "DRAFT PLACEHOLDER. This is not the final legal notice.",
  is_draft: true,
};

const json = (status: number, body: unknown) => ({
  status,
  contentType: "application/json",
  body: JSON.stringify(body),
});

async function mockApi(page: Page, initial: L[]) {
  const state = { learners: [...initial], posted: null as unknown, csrf: "" };
  await page.route("**/api/auth/me", (route) => route.fulfill(json(200, SESSION)));
  await page.route(/\/api\/learners/, async (route) => {
    const req = route.request();
    const path = new URL(req.url()).pathname;
    const method = req.method();
    if (path === "/api/learners/consent-notice") return route.fulfill(json(200, NOTICE));
    if (path === "/api/learners" && method === "GET") return route.fulfill(json(200, state.learners));
    if (path === "/api/learners" && method === "POST") {
      const body = req.postDataJSON() as { nickname: string; grade: number };
      state.posted = body;
      state.csrf = req.headers()["x-csrf-token"] ?? "";
      const created = { id: "new-" + state.learners.length, nickname: body.nickname, grade: body.grade };
      state.learners.push(created);
      return route.fulfill(json(201, created));
    }
    const id = path.split("/").pop();
    const index = state.learners.findIndex((l) => l.id === id);
    if (method === "PATCH" && index >= 0) {
      Object.assign(state.learners[index], req.postDataJSON());
      return route.fulfill(json(200, state.learners[index]));
    }
    if (method === "DELETE" && index >= 0) {
      state.learners.splice(index, 1);
      return route.fulfill({ status: 204 });
    }
    return route.fulfill(json(404, { detail: "Learner not found." }));
  });
  return state;
}

test("signed-out visitors are sent to sign in", async ({ page }) => {
  await page.route("**/api/auth/me", (route) => route.fulfill(json(401, { detail: "Not signed in." })));
  await page.goto("/learners");
  await expect(page).toHaveURL(/\/login$/);
});

test("shows an empty state and the consent notice", async ({ page }) => {
  await mockApi(page, []);
  await page.goto("/learners");
  await expect(page.getByRole("heading", { name: "Your learners" })).toBeVisible();
  await expect(page.getByText("No learners yet.")).toBeVisible();
  await expect(page.getByText("Draft placeholder, not the final legal notice")).toBeVisible();
});

test("adding a learner needs the consent box, then sends consent and the CSRF token", async ({ page }) => {
  const state = await mockApi(page, []);
  await page.goto("/learners");
  await page.getByLabel("Learner nickname").fill("Zuri");
  await page.getByLabel("Learner grade").selectOption("6");

  await page.getByRole("button", { name: "Add learner" }).click();
  await expect(page.getByText("Please tick the box to confirm consent.")).toBeVisible();
  expect(state.posted).toBeNull();

  await page.getByLabel(/parent or legal guardian/).check();
  await page.getByRole("button", { name: "Add learner" }).click();

  const card = page.getByRole("listitem").filter({ hasText: "Zuri" });
  await expect(card).toContainText("Grade 6");
  expect(state.posted).toEqual({
    nickname: "Zuri",
    grade: 6,
    consent: { notice_version: "0.1-draft", accepted: true },
  });
  expect(state.csrf).toBe("csrf-test-token");
});

test("personal data in a nickname is blocked before the API is called", async ({ page }) => {
  const state = await mockApi(page, []);
  await page.goto("/learners");
  await page.getByLabel("Learner nickname").fill("kid@example.com");
  await page.getByLabel(/parent or legal guardian/).check();
  await page.getByRole("button", { name: "Add learner" }).click();
  await expect(page.getByText(/no email addresses or phone numbers/).first()).toBeVisible();
  expect(state.posted).toBeNull();
});

test("a learner can be edited", async ({ page }) => {
  await mockApi(page, [{ id: "l1", nickname: "Zuri", grade: 6 }]);
  await page.goto("/learners");
  const card = page.getByRole("listitem").filter({ hasText: "Zuri" });
  await card.getByRole("button", { name: "Edit" }).click();
  await page.getByLabel("Edit grade").selectOption("7");
  await page.getByRole("button", { name: "Save" }).click();
  await expect(page.getByRole("listitem").filter({ hasText: "Zuri" })).toContainText("Grade 7");
});

test("removing a learner asks for confirmation first", async ({ page }) => {
  await mockApi(page, [{ id: "l1", nickname: "Zuri", grade: 6 }]);
  await page.goto("/learners");
  const card = page.getByRole("listitem").filter({ hasText: "Zuri" });
  await card.getByRole("button", { name: "Remove" }).click();
  await expect(page.getByText(/withdraws your consent/)).toBeVisible();
  await page.getByRole("button", { name: "Keep" }).click();
  await expect(page.getByRole("listitem").filter({ hasText: "Zuri" })).toBeVisible();

  await card.getByRole("button", { name: "Remove" }).click();
  await page.getByRole("button", { name: "Yes, remove" }).click();
  await expect(page.getByText("No learners yet.")).toBeVisible();
});
