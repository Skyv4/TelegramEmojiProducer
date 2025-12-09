import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('Home Page', () => {
  test('should allow file upload and display converted sticker', async ({ page }) => {
    await page.goto('/');

    // Expect a title "to contain" a substring.
    await expect(page).toHaveTitle(/Telegram Emoji Converter/);

    // Prepare a dummy file for upload
    const dummyFilePath = path.join(__dirname, '..', 'public', 'first_frame.png'); // Path to an existing file

    // Upload the file
    await page.setInputFiles('input[type="file"]', dummyFilePath);

    // Click the upload button
    await page.getByRole('button', { name: 'Upload and Convert' }).click();

    // Expect alert for successful upload (optional, based on your current UI)
    // await expect(page.locator('text=File uploaded successfully!')).toBeVisible();

    // Expect the video element to be visible
    await expect(page.locator('video')).toBeVisible({ timeout: 30000 }); // Increase timeout for conversion
    await expect(page.locator('video')).toHaveAttribute('src', /http:\/\/localhost:8000\/download\/.+\.webm/);
  });

  test('should allow URL input and display converted sticker', async ({ page }) => {
    await page.goto('/');

    // Expect a title "to contain" a substring.
    await expect(page).toHaveTitle(/Telegram Emoji Converter/);

    const imageUrl = 'https://media.giphy.com/media/efxaU94N0QhA355Txa/giphy.gif'; // A sample GIF URL

    // Fill the URL input
    await page.getByPlaceholder('Enter emoji URL').fill(imageUrl);

    // Click the convert from URL button
    await page.getByRole('button', { name: 'Convert from URL' }).click();

    // Expect alert for successful conversion (optional)
    // await expect(page.locator('text=URL converted successfully!')).toBeVisible();

    // Expect the video element to be visible
    await expect(page.locator('video')).toBeVisible({ timeout: 30000 }); // Increase timeout for conversion
    await expect(page.locator('video')).toHaveAttribute('src', /http:\/\/localhost:8000\/download\/.+\.webm/);
  });
});
