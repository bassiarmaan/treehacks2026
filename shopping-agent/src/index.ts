/**
 * Cortex Shopping Agent
 * Uses Stagehand (Browserbase) to automate product research and price comparison.
 * Exposes an Express API that the Python backend calls.
 */

import "dotenv/config";
import express from "express";
import { Stagehand } from "@browserbasehq/stagehand";
import { z } from "zod/v3";

const app = express();
app.use(express.json());

const PORT = process.env.SHOPPING_AGENT_PORT || 8002;

// -- Types -------------------------------------------------------------------

interface ProductResult {
  name: string;
  price: string;
  rating: string;
  url: string;
  source: string;
}

interface ShopResponse {
  query: string;
  results: ProductResult[];
  comparison: string;
}

// -- Stagehand Shopping Logic ------------------------------------------------

async function searchProducts(query: string): Promise<ShopResponse> {
  const stagehand = new Stagehand({
    env: process.env.BROWSERBASE_API_KEY ? "BROWSERBASE" : "LOCAL",
    enableCaching: true,
  });

  await stagehand.init();
  const page = stagehand.context.pages()[0];

  const results: ProductResult[] = [];

  try {
    // Search Google Shopping
    await page.goto(
      `https://www.google.com/search?q=${encodeURIComponent(query)}&tbm=shop`
    );

    // Wait for results to load
    await page.waitForTimeout(2000);

    // Extract product data
    const ProductSchema = z.object({
      products: z.array(
        z.object({
          name: z.string().describe("Product name/title"),
          price: z.string().describe("Product price including currency symbol"),
          rating: z
            .string()
            .describe("Star rating or review score, empty if not available"),
          source: z
            .string()
            .describe("Store/retailer name selling the product"),
        })
      ),
    });

    const extracted = await stagehand.extract(
      "Extract the top 5 product results with their names, prices, ratings, and store names",
      ProductSchema
    );

    for (const product of extracted.products.slice(0, 5)) {
      results.push({
        name: product.name,
        price: product.price,
        rating: product.rating || "N/A",
        url: `https://www.google.com/search?q=${encodeURIComponent(product.name)}&tbm=shop`,
        source: product.source,
      });
    }

    // Generate a comparison summary
    let comparison = `Found ${results.length} products for "${query}":\n`;
    for (let i = 0; i < results.length; i++) {
      const r = results[i];
      comparison += `${i + 1}. ${r.name} - ${r.price} from ${r.source} (${r.rating})\n`;
    }

    if (results.length > 0) {
      // Find the cheapest
      const prices = results
        .map((r) => {
          const match = r.price.match(/[\d,.]+/);
          return match ? parseFloat(match[0].replace(",", "")) : Infinity;
        })
        .filter((p) => isFinite(p));

      if (prices.length > 0) {
        const minPrice = Math.min(...prices);
        const cheapest = results.find((r) => r.price.includes(String(minPrice)));
        if (cheapest) {
          comparison += `\nBest deal: ${cheapest.name} at ${cheapest.price} from ${cheapest.source}`;
        }
      }
    }

    return { query, results, comparison };
  } catch (error) {
    console.error("Shopping search error:", error);
    return {
      query,
      results,
      comparison: `Could not complete search for "${query}". ${results.length} partial results found.`,
    };
  } finally {
    await stagehand.close();
  }
}

// -- Express Routes ----------------------------------------------------------

app.get("/health", (_req, res) => {
  res.json({ status: "ok", service: "cortex-shopping-agent" });
});

app.post("/shop", async (req, res) => {
  const { query } = req.body;
  if (!query) {
    return res.status(400).json({ error: "Missing 'query' field" });
  }

  console.log(`Shopping search: "${query}"`);

  try {
    const result = await searchProducts(query);
    res.json(result);
  } catch (error) {
    console.error("Shopping error:", error);
    res.status(500).json({
      error: "Shopping search failed",
      detail: error instanceof Error ? error.message : String(error),
    });
  }
});

// -- Start -------------------------------------------------------------------

app.listen(PORT, () => {
  console.log(`Cortex Shopping Agent running on port ${PORT}`);
  console.log(
    `Using ${process.env.BROWSERBASE_API_KEY ? "Browserbase cloud" : "local Chrome"} browser`
  );
});
