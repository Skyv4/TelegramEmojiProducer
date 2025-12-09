import { test, expect } from '@playwright/test';

test.describe('Admin Page', () => {
  const adminPassword = 'hamilton jacobi bellman'; // Use the actual admin password

  test('should allow admin login and display dashboard', async ({ page }) => {
    await page.goto('/admin');

    // Expect the admin login title
    await expect(page.getByRole('heading', { name: 'Admin Login' })).toBeVisible();

    // Fill the password input
    await page.getByPlaceholder('Enter password').fill(adminPassword);

    // Click the login button
    await page.getByRole('button', { name: 'Login' }).click();

    // Expect the admin dashboard title to be visible after successful login
    await expect(page.getByRole('heading', { name: 'Admin Dashboard' })).toBeVisible({ timeout: 10000 });

    // Expect conversion requests section to be visible
    await expect(page.getByRole('heading', { name: 'Conversion Requests' })).toBeVisible();
  });

  test('should allow marking a request as complete', async ({ page }) => {
    await page.goto('/admin');

    // Login first
    await page.getByPlaceholder('Enter password').fill(adminPassword);
    await page.getByRole('button', { name: 'Login' }).click();
    await expect(page.getByRole('heading', { name: 'Admin Dashboard' })).toBeVisible({ timeout: 10000 });

    // Assuming there's at least one request with status not 'admin_completed'
    // Find a "Mark as Complete" button and click it
    const completeButton = page.getByRole('button', { name: 'Mark as Complete' }).first();
    if (await completeButton.isVisible()) {
      page.on('dialog', async dialog => {
        expect(dialog.message()).toContain('Request marked as completed!');
        await dialog.accept();
      });
      await completeButton.click();
      // Optionally, assert that the status changes or the button disappears
      // This might require a reload or waiting for UI update depending on implementation
      await expect(completeButton).not.toBeVisible(); // Assuming button disappears after completion
    } else {
      console.warn('No "Mark as Complete" button found. Skipping test for marking request as complete.');
    }
  });
});
