# Product Intelligence Flow

The **Product Intelligence Agent** is responsible for mapping ambiguous customer requirements to specific, concrete product recommendations from the Demo App catalog.

## Location
- `app/agents/product_intelligence/agent.py`

## The Execution Flow

1. **Requirement Injection**: The agent receives a dictionary containing the extracted customer requirements (e.g., `{ "budget_max": 1500, "category": "laptop" }`).
2. **Pre-fetching Optimization (Speed Trick)**: Instead of handing the `search_products` tool directly to the LLM and forcing a slow multi-turn tool-call loop, the agent executes the search programmatically *before* invoking the LLM. 
   - It parses the requirements, builds query parameters (`max_price=1500`, `category=laptops`), and calls `demo_client.get_products()`.
   - It caps the result size to 5 to keep the prompt context small.
3. **LLM Prompting**: The retrieved catalog items are injected directly into the LLM prompt as JSON context. 
4. **ID Masking (Accuracy Trick)**: Real UUIDs (e.g. `123e4567-e89b...`) confuse LLMs. The Agent masks them with simple integer IDs (`1`, `2`, `3`) before sending them to the LLM. 
5. **Structured Output**: The LLM is forced via Langchain's `JsonOutputParser` to return a strictly structured array of `LightweightProductRecommendation` objects (using the integer IDs).
6. **Data Rehydration**: The Agent maps the integer IDs back to the real UUIDs and enriches the response with the exact data from the database (URLs, original prices, names) to ensure zero hallucination.

## Output Structure

The final output is a `ProductIntelligenceOutput` object containing:
- `recommendations`: The enriched product data.
- `comparison_summary`: An LLM-generated string comparing the options.
- `recommendation_summary`: A friendly summary string.
