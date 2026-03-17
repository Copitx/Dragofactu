import { expect, test } from "@playwright/test";

test("la app renderiza login", async ({ page }) => {
  await page.goto("/login");
  await expect(page).toHaveTitle(/Dragofactu/i);
  await expect(page.getByRole("button", { name: /login|iniciar/i })).toBeVisible();
});
