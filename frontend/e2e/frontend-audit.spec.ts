import { test, expect } from "@playwright/test";
import path from "path";
import fs from "fs";

test.describe("Sprint 7 — Frontend End-to-End Enterprise Test Suite", () => {
  test.beforeEach(async ({ page, context }) => {
    // Set viewport to standard desktop and clear auth state
    await page.setViewportSize({ width: 1440, height: 900 });
    await context.clearCookies();
  });

  test("1. Landing page loads correctly with all marketing sections", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/Gokul Text Print/i);

    // Verify main hero heading
    const heroHeading = page.locator("h1").first();
    await expect(heroHeading).toBeVisible();
    await expect(heroHeading).toContainText(/Autonomous AI|Industrial Textile/i);

    // Verify presence of primary navigation links
    await expect(page.locator('a[href="/features"]').first()).toBeVisible();
    await expect(page.locator('a[href="/pricing"]').first()).toBeVisible();
    await expect(page.locator('a[href="/login"]').first()).toBeVisible();
    await expect(page.locator('a[href="/register"]').first()).toBeVisible();

    // Verify key landing sections are present
    await expect(page.getByText(/Autonomous Intelligence Stack|System Architecture/i).first()).toBeVisible();
    await expect(page.getByText(/Intelligent Factory Automation/i).first()).toBeVisible();
  });

  test("2. Login flow routes directly to role-specific dashboard", async ({ page, context }) => {
    // ── Test CEO Login ──
    await page.goto("/login");
    await expect(page.locator("h1").first()).toContainText(/Sign In/i);

    // Verify the 2 enterprise role buttons exist
    const adminBtn = page.getByRole("button", { name: /Admin \(System/i });
    const ceoBtn = page.getByRole("button", { name: /CEO \(Executive/i });
    await expect(adminBtn).toBeVisible();
    await expect(ceoBtn).toBeVisible();

    // Click CEO quick fill and sign in
    await ceoBtn.click();
    await page.getByRole("button", { name: /Sign In/i }).click();

    // Verify direct landing on /dashboard
    await page.waitForURL("**/dashboard", { timeout: 15000 });
    expect(page.url()).toContain("/dashboard");
    await expect(page.getByRole("heading", { level: 1 }).first()).toContainText(/Executive Dashboard/i);

    // ── Test Admin Login ──
    // Clear cookies & storage so /login doesn't auto-redirect back to /dashboard
    await context.clearCookies();
    await page.evaluate(() => localStorage.clear());

    await page.goto("/login");
    await expect(page.locator("h1").first()).toContainText(/Sign In/i);
    await page.getByRole("button", { name: /Admin \(System/i }).click();
    await page.getByRole("button", { name: /Sign In/i }).click();

    // Verify direct landing on /admin
    await page.waitForURL("**/admin", { timeout: 15000 });
    expect(page.url()).toContain("/admin");
    await expect(page.getByRole("heading", { level: 1 }).first()).toContainText(/Admin Operations Center/i);
    await expect(page.getByText(/SYSTEM ROOT/i).first()).toBeVisible();
  });

  test("3. Dashboard loads with live KPI cards and trend charts", async ({ page }) => {
    // Log in as CEO to view dashboard
    await page.goto("/login");
    await page.getByRole("button", { name: /CEO \(Executive/i }).click();
    await page.getByRole("button", { name: /Sign In/i }).click();
    await page.waitForURL("**/dashboard");

    // Wait for live KPIs to load
    await expect(page.getByText(/Revenue|Net Sales/i).first()).toBeVisible();
    await expect(page.getByText(/Inventory|Health Score/i).first()).toBeVisible();

    // Verify charts render SVG elements
    const svgCharts = page.locator(".recharts-responsive-container");
    await expect(svgCharts.first()).toBeVisible({ timeout: 10000 });

    // Verify Quick Actions exist
    await expect(page.getByRole("button", { name: /Ask AI Copilot/i })).toBeVisible();
  });

  test("4. Navigation to each sidebar module page works cleanly", async ({ page }) => {
    await page.goto("/login");
    await page.getByRole("button", { name: /CEO \(Executive/i }).click();
    await page.getByRole("button", { name: /Sign In/i }).click();
    await page.waitForURL("**/dashboard");

    const modules = [
      { href: "/sales", titlePattern: /Demand Forecasting|Sales/i },
      { href: "/inventory", titlePattern: /Grey Cloth|Inventory/i },
      { href: "/copilot", titlePattern: /Copilot|Assistant/i },
      { href: "/knowledge", titlePattern: /Chemical Dye|Knowledge/i },
      { href: "/reports", titlePattern: /Intelligence Summaries|Reports/i },
      { href: "/alerts", titlePattern: /Operational Incident|Alert/i },
      { href: "/settings", titlePattern: /Mill & Model Configuration|Settings/i },
      { href: "/admin", titlePattern: /Admin Operations Center/i },
    ];

    for (const mod of modules) {
      await page.goto(mod.href);
      await expect(page).toHaveURL(new RegExp(mod.href));
      const heading = page.getByRole("heading", { level: 1 }).first();
      await expect(heading).toBeVisible({ timeout: 10000 });
      await expect(heading).toContainText(mod.titlePattern);
    }
  });

  test("5. AI Copilot sends a question and receives synthesized answer", async ({ page }) => {
    await page.goto("/login");
    await page.getByRole("button", { name: /CEO \(Executive/i }).click();
    await page.getByRole("button", { name: /Sign In/i }).click();
    await page.waitForURL("**/dashboard");

    await page.goto("/copilot");
    await page.waitForLoadState("networkidle");

    const textarea = page.getByPlaceholder(/Ask Executive Copilot/i);
    await expect(textarea).toBeVisible({ timeout: 10000 });

    // Send a real cross-functional question
    await textarea.fill("What is our forecasted sales demand for Pure Cotton 60s?");
    const sendBtn = page.locator('button[aria-label="Send message"]');
    await sendBtn.click();

    // Expect an assistant response bubble to appear
    await expect(page.getByText(/Executive Copilot/i).first()).toBeVisible({ timeout: 45000 });
    const responseBox = page.locator(".bg-card").filter({ hasText: /Executive Copilot/i }).first();
    await expect(responseBox).toBeVisible({ timeout: 45000 });
  });

  test("6. Document upload in Knowledge Center succeeds", async ({ page }) => {
    await page.goto("/login");
    await page.getByRole("button", { name: /CEO \(Executive/i }).click();
    await page.getByRole("button", { name: /Sign In/i }).click();
    await page.waitForURL("**/dashboard");

    await page.goto("/knowledge");
    await page.waitForLoadState("networkidle");

    // Verify document catalog table
    await expect(
      page.getByText(/Uploaded Technical Documents|Document Library/i).first()
    ).toBeVisible();

    // Read genuine test PDF and append unique comment for distinct hash
    const samplePdfBuf = fs.readFileSync(path.join(__dirname, "test_sop.pdf"));
    const uniquePdfBuf = Buffer.concat([samplePdfBuf, Buffer.from(`\n% timestamp_${Date.now()}`)]);
    const testPdfName = `e2e_sop_${Date.now()}.pdf`;
    const testPdfPath = path.join(process.cwd(), testPdfName);
    fs.writeFileSync(testPdfPath, uniquePdfBuf);

    try {
      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles(testPdfPath);

      // Verify file name appears in staging area
      await expect(page.getByText(testPdfName)).toBeVisible({ timeout: 5000 });

      // Click upload button
      const uploadBtn = page.getByRole("button", { name: /Upload Document/i });
      await uploadBtn.click();

      // Expect upload confirmation
      await expect(
        page.getByText(/uploaded successfully/i).first()
      ).toBeVisible({ timeout: 25000 });
    } finally {
      if (fs.existsSync(testPdfPath)) {
        fs.unlinkSync(testPdfPath);
      }
    }
  });

  test("7. Report download triggers successfully", async ({ page }) => {
    await page.goto("/login");
    await page.getByRole("button", { name: /CEO \(Executive/i }).click();
    await page.getByRole("button", { name: /Sign In/i }).click();
    await page.waitForURL("**/dashboard");

    await page.goto("/reports");
    await page.waitForLoadState("networkidle");

    // Verify report cadence tabs exist
    await expect(page.getByRole("button", { name: /Monthly/i })).toBeVisible();

    // Wait for the report download button
    const downloadPdfBtn = page.getByRole("button", { name: /Download PDF/i });
    await expect(downloadPdfBtn).toBeVisible({ timeout: 10000 });

    // Verify clicking triggers the download or network call to /api/reports/generate
    const [response] = await Promise.all([
      page.waitForResponse(
        (res) => res.url().includes("/api/reports/generate") && res.status() === 200,
        { timeout: 15000 }
      ),
      downloadPdfBtn.click(),
    ]);

    expect(response.status()).toBe(200);
  });

  test("8. Alert resolution updates alert status", async ({ page }) => {
    await page.goto("/login");
    await page.getByRole("button", { name: /CEO \(Executive/i }).click();
    await page.getByRole("button", { name: /Sign In/i }).click();
    await page.waitForURL("**/dashboard");

    await page.goto("/alerts");
    await page.waitForLoadState("networkidle");

    // Verify the 4 domain sections render
    await expect(page.getByText(/Critical Priority Incidents/i).first()).toBeVisible();
    await expect(page.getByText(/Low Stock & Fabric Buffers/i).first()).toBeVisible();
    await expect(page.getByText(/Sales Drop & Corridor Anomalies/i).first()).toBeVisible();
    await expect(page.getByText(/Model Errors & ETL Integrity/i).first()).toBeVisible();

    // Check if there is an active "Mark as Resolved" button
    const resolveBtn = page.getByRole("button", { name: /Mark as Resolved/i }).first();
    if (await resolveBtn.isVisible()) {
      await resolveBtn.click();
      // Verify success notice or resolved badge
      await expect(
        page.getByText(/marked as resolved|RESOLVED/i).first()
      ).toBeVisible({ timeout: 10000 });
    } else {
      // If all alerts already resolved, confirm resolved badges or all clear state exists
      await expect(page.getByText(/RESOLVED|All Clear/i).first()).toBeVisible();
    }
  });
});
