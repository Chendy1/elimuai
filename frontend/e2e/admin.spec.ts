import { expect, test, type Page } from "@playwright/test";
import type { ReviewStatus, VersionTree } from "../lib/types";

const json = (status: number, body: unknown) => ({
  status,
  contentType: "application/json",
  body: JSON.stringify(body),
});

const session = (roles: string[]) => ({
  user: { id: "u1", email: "staff@example.com", display_name: "Staff" },
  csrf_token: "csrf-test-token",
  roles,
});

function fakeTree(): VersionTree {
  return {
    id: "v1", label: "Draft 2026", status: "draft",
    grades: [{
      id: "g1", level: 6, name: "Grade 6",
      learning_areas: [{
        id: "a1", name: "Demo Mathematics", sort_order: 0, archived: false,
        review_status: "draft", review_comment: null, source_page_id: null,
        strands: [{
          id: "s1", number: "1.0", name: "Demo Strand", unit_id: null,
          review_status: "draft", review_comment: null, source_page_id: "p1",
          rubric: [{ indicator: "Ability to demo", exceeds: "E", meets: "M", approaches: "A", below: "B" }],
          sub_strands: [{
            id: "x1", number: "1.1", name: "Demo Sub-strand", suggested_lessons: 5, link_to_other_areas: null,
            topics: ["Demo topic"], outcomes: [{ code: "a", text: "Demo outcome one" }],
            experiences: ["Demo experience"], inquiry_questions: ["What is a demo?"],
            competencies: [{ code: "critical_thinking", name: "Critical Thinking and Problem Solving", description: "learner demos" }],
            values: [{ name: "Unity", description: "together" }], pcis: [],
            review_status: "draft", source_page_id: "p1",
            review_comment: "Auto-extracted from PDF pages 13-14. Check against the source page.",
          }],
        }],
      }],
    }],
  };
}

const PAGES: Record<string, object> = {
  p1: { id: "p1", source_id: "src", source_title: "Demo design", license_status: "not_requested", pdf_page: 13,
        printed_page: "13", text: "DEMO PAGE ONE", previous_page_id: null, next_page_id: "p2" },
  p2: { id: "p2", source_id: "src", source_title: "Demo design", license_status: "not_requested", pdf_page: 14,
        printed_page: null, text: "DEMO PAGE TWO", previous_page_id: "p1", next_page_id: null },
};

async function mockAdmin(page: Page, roles: string[]) {
  const state = {
    tree: fakeTree(),
    reviews: [] as { body: Record<string, unknown>; csrf: string }[],
    edits: [] as { body: Record<string, unknown>; csrf: string }[],
  };
  await page.route("**/api/auth/me", (route) => route.fulfill(json(200, session(roles))));
  await page.route(/\/api\/admin\/curriculum\//, async (route) => {
    const req = route.request();
    const path = new URL(req.url()).pathname.replace("/api/admin/curriculum", "");
    const method = req.method();
    const area = state.tree.grades[0].learning_areas[0];
    const strand = area.strands[0];
    const sub = strand.sub_strands[0];

    if (method === "GET" && path === "/curricula")
      return route.fulfill(json(200, [{ id: "c1", code: "demo-cbe", name: "Demo curriculum", country_code: "KE" }]));
    if (method === "GET" && path === "/curricula/c1/versions")
      return route.fulfill(json(200, [{ id: "v1", curriculum_id: "c1", label: "Draft 2026", status: "draft", published_at: null }]));
    if (method === "GET" && path === "/versions/v1/tree") return route.fulfill(json(200, state.tree));
    if (method === "GET" && path.startsWith("/source-pages/"))
      return route.fulfill(json(200, PAGES[path.split("/").pop() as string]));
    if (method === "POST" && path === "/review") {
      const body = req.postDataJSON() as { kind: string; id: string; status: ReviewStatus; comment?: string };
      state.reviews.push({ body, csrf: req.headers()["x-csrf-token"] ?? "" });
      const node = body.kind === "learning_area" ? area : body.kind === "strand" ? strand : sub;
      node.review_status = body.status;
      if (body.comment !== undefined) node.review_comment = body.comment;
      return route.fulfill({ status: 204 });
    }
    if (method === "PATCH" && path === "/sub-strands/x1") {
      const body = req.postDataJSON() as Record<string, unknown>;
      state.edits.push({ body, csrf: req.headers()["x-csrf-token"] ?? "" });
      Object.assign(sub, body, { review_status: "draft" });
      return route.fulfill(json(200, { id: "x1", number: "1.1", name: sub.name, review_status: "draft" }));
    }
    if (method === "POST" && path === "/versions/v1/publish") {
      const open = [area, strand, sub].filter((n) => n.review_status !== "approved").length;
      if (open > 0)
        return route.fulfill(json(409, { detail: { message: "All content must be approved before publishing.",
          details: { unapproved: { learning_area: 0, strand: 1, sub_strand: 1 } } } }));
      state.tree.status = "published";
      return route.fulfill(json(200, { id: "v1", status: "published" }));
    }
    return route.fulfill(json(404, { detail: "Not found." }));
  });
  return state;
}

test("people without a review role are told they have no access", async ({ page }) => {
  await mockAdmin(page, ["guardian"]);
  await page.goto("/admin/curriculum");
  await expect(page.getByText("does not have access to curriculum review")).toBeVisible();
});

test("signed-out visitors are sent to sign in", async ({ page }) => {
  await page.route("**/api/auth/me", (route) => route.fulfill(json(401, { detail: "Not signed in." })));
  await page.goto("/admin/curriculum");
  await expect(page).toHaveURL(/\/login$/);
});

test("the list links to a version, which opens the review screen", async ({ page }) => {
  await mockAdmin(page, ["content_reviewer"]);
  await page.goto("/admin/curriculum");
  await expect(page.getByText("Demo curriculum")).toBeVisible();
  await page.getByRole("link", { name: "Draft 2026" }).click();
  await expect(page.getByRole("heading", { name: "Review: Draft 2026" })).toBeVisible();
  await expect(page.getByTestId("progress")).toContainText("0 of 1 sub-strands approved");
});

test("selecting a sub-strand shows the draft record beside its source page", async ({ page }) => {
  await mockAdmin(page, ["content_reviewer"]);
  await page.goto("/admin/curriculum/v1");
  await page.getByRole("button", { name: /1\.1 Demo Sub-strand/ }).click();
  await expect(page.getByRole("heading", { name: "1.1 Demo Sub-strand" })).toBeVisible();
  await expect(page.getByText("a) Demo outcome one")).toBeVisible();
  await expect(page.getByText(/Auto-extracted from PDF pages 13-14/)).toBeVisible();
  await expect(page.getByTestId("source-text")).toHaveText("DEMO PAGE ONE");

  await page.getByRole("button", { name: "Next page" }).click();
  await expect(page.getByTestId("source-text")).toHaveText("DEMO PAGE TWO");
  await page.getByRole("button", { name: "Previous page" }).click();
  await expect(page.getByTestId("source-text")).toHaveText("DEMO PAGE ONE");
});

test("approving sends the decision, the comment and the CSRF token", async ({ page }) => {
  const state = await mockAdmin(page, ["content_reviewer"]);
  await page.goto("/admin/curriculum/v1");
  await page.getByRole("button", { name: /1\.1 Demo Sub-strand/ }).click();
  await page.getByLabel("Comment (optional)").fill("Matches the source");
  await page.getByRole("button", { name: "Approve", exact: true }).click();
  await expect(page.getByTestId("detail-status")).toHaveText("Approved");
  await expect(page.getByTestId("progress")).toContainText("1 of 1 sub-strands approved");
  expect(state.reviews[0].body).toEqual({ kind: "sub_strand", id: "x1", status: "approved", comment: "Matches the source" });
  expect(state.reviews[0].csrf).toBe("csrf-test-token");

  await page.getByRole("button", { name: "Needs changes" }).click();
  await expect(page.getByTestId("detail-status")).toHaveText("Needs changes");
  expect(state.reviews[1].body).toEqual({ kind: "sub_strand", id: "x1", status: "rejected" }); // no comment key
});

test("reviewers cannot publish, admins can, and publishing explains what is missing", async ({ page }) => {
  await mockAdmin(page, ["content_reviewer"]);
  await page.goto("/admin/curriculum/v1");
  await expect(page.getByRole("heading", { name: "Review: Draft 2026" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Publish version" })).toHaveCount(0);

  const admin = await page.context().newPage();
  await mockAdmin(admin, ["curriculum_admin"]);
  await admin.goto("/admin/curriculum/v1");
  await admin.getByRole("button", { name: "Publish version" }).click();
  await expect(admin.getByText(/All content must be approved before publishing/)).toBeVisible();
  await expect(admin.getByText(/Still to approve: 1 strand, 1 sub strand/)).toBeVisible();

  for (const name of [/Demo Mathematics/, /Strand 1\.0 Demo Strand/, /1\.1 Demo Sub-strand/]) {
    await admin.getByRole("button", { name }).first().click();
    await admin.getByRole("button", { name: "Approve", exact: true }).click();
    await expect(admin.getByTestId("detail-status")).toHaveText("Approved");
  }
  await admin.getByRole("button", { name: "Publish version" }).click();
  await expect(admin.getByText("Published. Learners can now see this version.")).toBeVisible();
});

test("a curriculum admin can edit a record, and it goes back to draft", async ({ page }) => {
  const state = await mockAdmin(page, ["curriculum_admin"]);
  await page.goto("/admin/curriculum/v1");
  await page.getByRole("button", { name: /1\.1 Demo Sub-strand/ }).click();
  await page.getByRole("button", { name: "Approve", exact: true }).click();
  await expect(page.getByTestId("detail-status")).toHaveText("Approved");

  await page.getByRole("button", { name: "Edit record" }).click();
  await page.getByLabel("Topics").fill("Demo topic\nSecond topic");
  await page.getByLabel("Specific learning outcomes").fill("a) Demo outcome one\nb) New outcome");
  await page.getByRole("button", { name: "Save changes" }).click();

  await expect(page.getByText("b) New outcome")).toBeVisible();
  await expect(page.getByTestId("detail-status")).toHaveText("Draft");
  expect(state.edits[0].csrf).toBe("csrf-test-token");
  expect(state.edits[0].body).toEqual({
    name: "Demo Sub-strand", suggested_lessons: 5, link_to_other_areas: null,
    topics: ["Demo topic", "Second topic"],
    outcomes: [{ code: "a", text: "Demo outcome one" }, { code: "b", text: "New outcome" }],
    experiences: ["Demo experience"], inquiry_questions: ["What is a demo?"],
    competencies: [{ code: "critical_thinking", description: "learner demos" }],
    values: [{ name: "Unity", description: "together" }], pcis: [],
  });
});

test("the edit form rejects unknown competencies before calling the API", async ({ page }) => {
  const state = await mockAdmin(page, ["curriculum_admin"]);
  await page.goto("/admin/curriculum/v1");
  await page.getByRole("button", { name: /1\.1 Demo Sub-strand/ }).click();
  await page.getByRole("button", { name: "Edit record" }).click();
  await page.getByLabel("Core competencies").fill("Made up skill: x");
  await page.getByRole("button", { name: "Save changes" }).click();
  await expect(page.getByText(/Unknown core competency: Made up skill/)).toBeVisible();
  expect(state.edits).toHaveLength(0);
});

test("reviewers do not see the edit button", async ({ page }) => {
  await mockAdmin(page, ["content_reviewer"]);
  await page.goto("/admin/curriculum/v1");
  await page.getByRole("button", { name: /1\.1 Demo Sub-strand/ }).click();
  await expect(page.getByRole("heading", { name: "1.1 Demo Sub-strand" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Edit record" })).toHaveCount(0);
});
