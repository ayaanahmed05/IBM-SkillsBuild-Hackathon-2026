# IBM watsonx.ai / Granite setup

MomentGuard v2.2 includes a real IBM Cloud runtime integration for the **explanation layer**. The deterministic MomentGuard engine remains authoritative for GO / WAIT / STAY / RETURN. Granite cannot change the decision.

## What you need

1. An IBM Cloud account with access to watsonx.ai.
2. A watsonx project. Copy its **Project ID** from the project Manage/General details page.
3. An IBM Cloud API key.
4. A Granite model ID available to your account/region.

IBM's current API supports model chat through `POST /ml/v1/text/chat`, using a model ID plus a project or space ID. The application obtains an IBM IAM bearer token server-side and never exposes the API key to the browser.

## Configure

Copy `backend/.env.example` to `backend/.env` and set:

```env
WATSONX_API_KEY=your_real_key
WATSONX_PROJECT_ID=your_project_id
WATSONX_URL=https://us-south.ml.cloud.ibm.com
WATSONX_MODEL_ID=the_granite_model_id_available_to_your_account
WATSONX_API_VERSION=2024-05-31
```

Do **not** commit `backend/.env`.

## Run

Restart the backend, then open:

- `http://127.0.0.1:4000/api/ibm/status` — should show `configured: true`.
- MomentGuard → Judge Mode → Proof Center → **Run IBM Granite explanation**.

A successful call creates a verified runtime trace containing the provider, model, latency, and the generated explanation. The Proof Center badge changes to **VERIFIED**.

## Safety boundary

Granite receives only the already-computed decision evidence and is instructed to explain it in 1–2 sentences without changing action or destination. If IBM Cloud is unavailable, the call fails safely and the deterministic recommendation remains active.

## Demo wording after a successful call

> MomentGuard uses IBM watsonx.ai on IBM Cloud to generate grounded, fan-facing explanations, while our deterministic safety engine retains final authority over GO, WAIT, STAY, and RETURN.
