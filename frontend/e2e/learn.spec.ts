import { expect, test, type Page } from "@playwright/test";

const json = (status: number, body: unknown) => ({
  status,
  contentType: "application/json",
  body: JSON.stringify(body),
});

const session = (roles: string[]) => ({
  user: { id: "u1", email: "person@example.com", display_name: "Person" },
  csrf_token: "csrf-test-token",
  roles,
});

const TREE = {
  id: "a1", name: "Demo Mathematics",
  strands: [{
    id: "s1", number: "1.0", name: "Demo Strand",
    sub_strands: [{
      id: "x1", number: "1.1", name: "Demo Sub-strand", suggested_lessons: 5,
      topics: ["Demo topic"], outcomes: [{ code: "a", text: "Demo outcome one" }],
      inquiry_questions: ["What is a demo?"],
    }],
  }],
  sources: [{ title: "Demo design", publisher: "Demo publisher" }],
  version: { id: "v1", label: "Draft 2026", status: "draft" },
};

async function mockLearn(
  page: Page,
  opts: { roles: string[]; learners: object[] | "forbidden"; areasStatus?: number },
) {
  const seen: string[] = [];
  await page.route("**/api/auth/me", (route) => route.fulfill(json(200, session(opts.roles))));
  await page.route(/\/api\/(learners|curriculum)/, async (route) => {
    const url = new URL(route.request().url());
    seen.push(url.pathname + url.search);
    if (url.pathname === "/api/learners") {
      return opts.learners === "forbidden"
        ? route.fulfill(json(403, { detail: "You do not have permission to do that." }))
        : route.fulfill(json(200, opts.learners));
    }
    if (url.pathname === "/api/curriculum/grades/6/learning-areas") {
      return opts.areasStatus === 404
        ? route.fulfill(json(404, { detail: "No published curriculum is available yet." }))
        : route.fulfill(json(200, [{ id: "a1", name: "Demo Mathematics" }]));
    }
    if (url.pathname === "/api/curriculum/learning-areas/a1") return route.fulfill(json(200, TREE));
    return route.fulfill(json(404, { detail: "Not found." }));
  });
  return seen;
}

const ZURI = [{ id: "l1", nickname: "Zuri", grade: 6 }];

test("a learner picks a subject, then a topic, and sees what it covers", async ({ page }) => {
  const seen = await mockLearn(page, { roles: ["guardian"], learners: ZURI });
  await page.goto("/learn");
  await expect(page.getByRole("heading", { name: "Hello, Zuri!" })).toBeVisible();
  await page.getByRole("link", { name: "Demo Mathematics" }).click();

  await expect(page.getByRole("heading", { level: 1, name: "Demo Mathematics" })).toBeVisible();
  await page.getByRole("button", { name: /1\.1 Demo Sub-strand/ }).click();
  await expect(page.getByRole("heading", { name: "1.1 Demo Sub-strand" })).toBeVisible();
  await expect(page.getByText("Demo outcome one")).toBeVisible();
  await expect(page.getByText("What is a demo?")).toBeVisible();
  await expect(page.getByText("Lessons for this topic are coming soon.")).toBeVisible();
  await expect(page.getByTestId("attribution")).toContainText("Demo publisher, Demo design");
  expect(seen.some((u) => u.includes("version_id"))).toBe(false);
});

test("without a learner profile the page asks for one first", async ({ page }) => {
  await mockLearn(page, { roles: ["guardian"], learners: [] });
  await page.goto("/learn");
  await expect(page.getByText("Add a learner first")).toBeVisible();
  await expect(page.getByRole("link", { name: "Add a learner" })).toBeVisible();
});

test("an unpublished curriculum shows a friendly message", async ({ page }) => {
  await mockLearn(page, { roles: ["guardian"], learners: ZURI, areasStatus: 404 });
  await page.goto("/learn");
  await expect(page.getByText(/not ready yet/)).toBeVisible();
});

test("staff can preview a draft version as a learner would see it", async ({ page }) => {
  const seen = await mockLearn(page, { roles: ["curriculum_admin"], learners: "forbidden" });
  await page.goto("/learn?version=v1&grade=6");
  await expect(page.getByText("Staff preview", { exact: true })).toBeVisible();
  await page.getByRole("link", { name: "Demo Mathematics" }).click();
  await expect(page.getByText(/Staff preview of Draft 2026 \(draft\)/)).toBeVisible();
  expect(seen).toContain("/api/curriculum/grades/6/learning-areas?version_id=v1");
  expect(seen).toContain("/api/curriculum/learning-areas/a1?version_id=v1");
});

test("people who are not reviewers cannot preview a version", async ({ page }) => {
  await mockLearn(page, { roles: ["guardian"], learners: ZURI });
  await page.goto("/learn?version=v1");
  await expect(page.getByText("Only reviewers can preview an unpublished version.")).toBeVisible();
});

test("staff accounts without a guardian role are pointed to guardian accounts", async ({ page }) => {
  await mockLearn(page, { roles: ["content_reviewer"], learners: "forbidden" });
  await page.goto("/learn");
  await expect(page.getByText(/Learning is for guardians and their learners/)).toBeVisible();
});

test("signed-out visitors are sent to sign in", async ({ page }) => {
  await page.route("**/api/auth/me", (route) => route.fulfill(json(401, { detail: "Not signed in." })));
  await page.goto("/learn");
  await expect(page).toHaveURL(/\/login$/);
});
