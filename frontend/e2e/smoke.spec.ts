import { expect, test } from "@playwright/test";

test("home page shows the headline and grade coverage", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { level: 1, name: "A smarter way to learn. Built for Kenya." }),
  ).toBeVisible();
  await expect(page.getByText("Grade 4", { exact: true })).toBeVisible();
  await expect(page.getByText("Grade 9", { exact: true })).toBeVisible();
});

test("footer states ElimuAI is not endorsed by official bodies", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("contentinfo").getByText(/not endorsed by KICD/)).toBeVisible();
});

test("navigation reaches How it works", async ({ page }) => {
  await page.goto("/");
  await page
    .getByRole("navigation", { name: "Main" })
    .getByRole("link", { name: "How it works" })
    .click();
  await expect(page.getByRole("heading", { level: 2, name: "How it works" })).toBeVisible();
});

test("primary call to action leads to the honest start page", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: /^Start Learning/ }).click();
  await expect(page).toHaveURL(/\/start$/);
  await expect(page.getByRole("heading", { name: "Registration is not open yet" })).toBeVisible();
});

test("privacy and terms are clearly marked as placeholders", async ({ page }) => {
  for (const path of ["/privacy", "/terms"]) {
    await page.goto(path);
    await expect(page.getByText("Draft placeholder")).toBeVisible();
  }
});

test.describe("mobile", () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test("menu opens and navigates", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "Open menu" }).click();
    await page
      .getByRole("navigation", { name: "Mobile" })
      .getByRole("link", { name: "How it works" })
      .click();
    await expect(page).toHaveURL(/\/how-it-works$/);
  });
});