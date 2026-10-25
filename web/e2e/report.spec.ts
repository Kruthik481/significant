import { expect, test } from '@playwright/test';

test('run a sample, read the verdict, open the share link', async ({ page }) => {
  await page.goto('/');
  await page.getByTestId('sample-checkout_win').click();
  await expect(page).toHaveURL(/\/r\/[\w-]{10}$/);
  await expect(page.getByTestId('verdict')).toContainText('Treatment wins');
  await expect(page.getByTestId('sequential-chart')).toBeVisible();
  if (process.env.SHOT) {
    // README image: let the red-pen marks finish drawing first
    await page.setViewportSize({ width: 1280, height: 1100 });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: '../docs/report.png' });
  }
  const url = page.url();
  await page.goto(url);
  await expect(page.getByTestId('verdict')).toContainText('Treatment wins');
  await page.goto('/r/doesnotexist');
  await expect(page.getByText(/report not found/i)).toBeVisible();
});
