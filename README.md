# Curato: Edge AI Itinerary Planner

Curato is a real-time itinerary planning app designed to generate **personalized, unique day plans** based on real-world constraints like location, time, companion, and budget — all running entirely on-device using quantized LLMs on Snapdragon® X Elite.

Curato automates the **tedious decision-making process**, intelligently selecting the best route and venues with emotional context — and delivering it all as a narrative-style plan that feels human.

> **All AI inference is performed locally**, without offloading any computation to the cloud. This ensures **data privacy**, **ultra-low latency**, and true spontaneity — even in low-connectivity environments.

Built with multiple quantized LLMs, Curato **divides lightweight and heavyweight tasks** across models to balance efficiency and quality. It uses **dynamic prompt generation** based on real-time user inputs and **locally caches location data** to minimize unnecessary network calls.

Each prompt is dynamically crafted based on user preferences like location, time, and companion, enabling the LLM to respond with high contextual accuracy and deliver a uniquely tailored plan with every generation.

---

## Edge AI Architecture

Curato uses a **multi-model architecture** designed specifically for real-time, on-device itinerary generation:

- **Phi 3.5 Mini** (quantized):  
  A lightweight LLM that filters and selects top-rated locations based on distance and category relevance.
- **Qwen2.5‑7B‑Instruct** (quantized):  
  Evaluated as a potential substitute for Phi 3.5 Mini, offering comparable or better speed and efficiency in lightweight selection tasks.
- **Llama‑v3.2‑3B‑Instruct** (quantized):  
  A heavier LLM that generates the final course narrative and detailed daily story using the user’s context.

All models are quantized and executed entirely on-device using **Qualcomm’s Genie SDK**, running on the **Snapdragon X Elite’s NPU** for low-latency and energy-efficient inference.

To reduce network usage, **place data is locally cached and filtered** after retrieval from the Kakao Map API. This improves consistency and responsiveness.

> **Note:** *Phi 3.5 Mini was not profiled because it is not officially available on Qualcomm AI Hub as of submission time.*

---

## Privacy & Trust

Planning a day with AI may not involve government IDs or credit cards — but it still requires personal context:
- Real-time location  
- Companion or relationship type (e.g., “I’m with my girlfriend”)  
- Budget and time availability  

Even though this isn’t traditionally classified as “sensitive data,” it reveals intent, habits, emotional state, and social context: aspects of daily life users may prefer to keep private.

Most AI services send this data to the cloud.  
**Curato doesn’t.** All reasoning and generation happens entirely on-device.

This enables:
- **True privacy** for spontaneous decisions, without outside exposure  
- **Offline functionality** in low-connectivity environments  
- **Higher trust**, especially in emotionally sensitive or socially private situations


---

## Why Edge AI?

Curato is specifically architected for on-device execution to meet the demands of real-time, privacy-sensitive, and network-independent itinerary planning. Rather than relying on external cloud infrastructure, all AI reasoning—including location selection, context-aware ordering, and narrative generation—is performed locally using quantized language models.

This design offers the following advantages:

- **Low latency:** Inference is executed directly on the device, enabling immediate response to user input.
- **Privacy preservation:** Sensitive user context—such as real-time location, time availability, and companion identity (e.g., a romantic partner or family member)—is processed entirely on-device. This prevents the exposure of personally identifiable information to external servers, which is especially critical in scenarios involving relationship dynamics or situational intent that users may not wish to disclose.
- **Offline readiness:** Cached place data allows Curato to operate reliably even in low-connectivity environments.
- **Energy-efficient processing:** Quantized models running on the Snapdragon NPU optimize for both performance and power efficiency.
- **Robustness and reliability:** By avoiding cloud dependencies, Curato ensures consistent availability and reduced operational risk.

Edge AI enables Curato to function as a trusted, context-aware assistant that delivers personalized itineraries securely and responsively—regardless of network conditions. Curato demonstrates real-time on-device inference, privacy-preserving architecture, and practical responsiveness that cannot be achieved through traditional server-based approaches.

---

## Key Features

| Component                      | Description |
|-------------------------------|-------------|
| LLM-based Place Selection      | Lightweight LLM selects top places per category |
| AI Narrative Generation        | Heavy LLM composes a human-like itinerary |
| Dynamic Prompting              | Prompts are generated from time, location, and companion context |
| On-Device AI Inference         | Quantized LLMs run locally using Genie SDK |
| Real-time KakaoMap Integration | Embedded WebView showing location markers |
| Secure API Key Handling        | `.env` system with encrypted injection — keys never exposed |

---

## Team Members
| Name | Role | Email | Qualcomm ID |
|------|------|-------|-------------|
| Sungwoo Jeon | AI Engineer / Fullstack Dev | [sungwoo100604@email.com] | [sungwoo100604@gmail.com] |
| Gain Lee | UI/UX Designer | [gain20570000@gmail.com] | [gain20570000@gmail.com] |

---

## Installation Instructions (Snapdragon X Elite)

> ⚠️ Requires Windows on Snapdragon (Snapdragon X Elite)

### 1. Prerequisites
Install the following system-wide dependencies:
| Tool                                                               | Version                                  | Purpose                                            |
| ------------------------------------------------------------------ | ---------------------------------------- | -------------------------------------------------- |
| [.NET SDK](https://dotnet.microsoft.com/en-us/download/dotnet/7.0) | 7.0+                                     | Build & run WPF UI                                 |
| [Python](https://www.python.org/downloads/release/python-3100/)    | 3.10                                     | Environment for model prep and export              |
| [Git](https://git-scm.com/)                                        | latest                                   | Required by Hugging Face and qai-hub-models        |
| [QAIRT SDK](https://qpm.qualcomm.com/)                             | 2.28.0+                                  | RQuantized model execution pipeline                |
| Genie SDK                                                          | Bundled with QAIRT                       | Required for `genie-t2t-run` model execution       | 

> Genie SDK is included in QAIRT SDK/bin and lib, and should be copied into your genie_bundle.

```bash
# Clone the repository
git clone https://github.com/yourusername/curato
cd curato
```

### 2. Set Up Python Environment
Create and activate a virtual environment:
```bash
python3.10 -m venv llm_env
source llm_env/bin/activate  # On Windows: llm_env\Scripts\activate
```

### 3. Install Required Python Packages
```bash
pip install torch==2.1.2 torchvision==0.16.2
pip install transformers==4.45.0 datasets==2.14.5
pip install huggingface-hub==0.23.1 pyarrow==15.0.2 psutil>=5.9
pip install cryptography requests
pip install qai-hub-models==0.32.0
```

```bash
pip install -U "qai-hub-models[llama-v3-2-3b-instruct]"
```
Replace `llama-v3-2-3b-instruct` with the desired llama model from [AI Hub
Model](https://github.com/quic/ai-hub-models/tree/main/qai_hub_models/models).
Note to replace `_` with `-` (e.g. `llama_v3_2_3b_instruct` -> `llama-v3-2-3b-instruct`)

### 4. Export Quantized LLMs
export your own model bundle:
```bash
python -m qai_hub_models.models.llama_v3_2_3b_instruct.export --device "Snapdragon X Elite CRD" --skip-inferencing --skip-profiling --output-dir genie_bundle
```

### 5. Prepare Genie Assets
Ensure the following files are placed in genie_bundle/:

.bin model files

tokenizer.json from Hugging Face

genie_config.json

htp_backend_ext_config.json

For Snapdragon X Elite:

```json
"soc_model": 60,
"dsp_arch": "v73"
```

Copy Genie executables and libraries from QAIRT SDK:
```bash
cp $QNN_SDK_ROOT/bin/aarch64-windows-msvc/genie-t2t-run.exe genie_bundle
cp $QNN_SDK_ROOT/lib/aarch64-windows-msvc/*.dll genie_bundle
```

### 6. Configure Secure API Keys
Add this to a .env file at the project root:
```bash
KAKAO_API_KEY=your_kakao_api_key
```

API keys are encrypted and safely managed during development to prevent leaks. The repository uses a .env-based system with secure key injection for local testing.

### 7. Build & Run the WPF App
```bash
dotnet run --project Curato
```

---

## Usage

Upon launch, the application opens with the main input interface (`SearchPage.xaml`), where users are guided to enter key trip parameters:

> • **Starting location** — Korean or English input with Kakao keyword search and autocomplete  
> • **Companion type** — Family, Friends, Partner, or Solo  
> • **Budget** — Low, Medium, or High  
> • **Start time** — Time periods and specific hour slots 
> • **Preferred place types** — Multi-selection from predefined tags  

Users can either type a custom location into the search box — supported by debounced Kakao Map autocomplete — or select from five popular preset regions shown below.

Once the inputs are set, clicking the **Generate** button initiates the on-device planning process.

First, a **lightweight quantized LLM** filters all candidate places retrieved from Kakao Map API and selects the **four most suitable locations**, based on user preferences and preset filters mapped to their companion type.

These selected locations are then passed to a **larger LLM**, which composes a narrative-style daily itinerary with a unique tone and activities tailored to both the companion type and selected budget — ensuring a deeply personalized result every time.

Once inference is complete, the app transitions to the output interface (`OutputPage.xaml`), displaying:
- A **Kakao Map** on the left with four markers arranged in visit order  
- A fully generated **emotional daily plan** on the right  
- A top bar showing the user’s input summary  

Users may click Edit Plan to re-generate at any time.

---

## Screenshots
[Youtube link]()

#### 1. Input Interface (Search Page)
Shows the user’s search flow, companion/budget/time selection, and suggested areas.

![SearchPage](./screenshots/SearchPage.png)

#### 2. Autocomplete in Action
Location search with debounced Kakao Map API keyword recommendations.

![Search Autocomplete](./screenshots/SearchBar_click.png)

#### 3. Loading Animation
On-device inference in progress after clicking the Generate button.

![Loading](./screenshots/LoadingPage.png)

#### 4. Output Interface (Map + Narrative)
Curato displays a generated emotional story and Kakao map with visit order.

![Output with Map](./screenshots/OutputPage.png)

#### 5. Hover Interaction (Optional)
When user clicks into generated places or edits plan.

![Click View](./screenshots/OutputPage_click.png)

---

## License

This project is licensed under the [MIT License](./LICENSE).

---

## Open Source Dependencies

Curato relies on the following open-source tools and models:

- **[Kakao Map API](https://developers.kakao.com/docs/latest/en/local/dev-guide)** – Provides geocoding and keyword search functionality via REST endpoints :contentReference[oaicite:1]{index=1}  
- **[QAIRT SDK](https://docs.qualcomm.com/bundle/publicresource/topics/80-70017-15B/qairt-install.html)** – Qualcomm’s AI Runtime SDK, required for running quantized LLMs on Snapdragon devices :contentReference[oaicite:2]{index=2}  
- **[Phi 3.5 Mini Instruct](https://aihub.qualcomm.com/compute/models/phi_3_5_mini_instruct?domain=Generative+AI&useCase=Text+Generation&chipsets=qualcomm-snapdragon-x-elite)** – Compact version of Microsoft’s Phi-3.5 language model, available in quantized formats suitable for on-device inference :contentReference[oaicite:3]{index=3}  
- **[Llama‑v3.2‑3B‑Instruct](https://aihub.qualcomm.com/models/llama_v3_2_3b_instruct)** – Meta’s instruction-tuned Llama 3.2 (3B) model, optimized and quantized for on‑device use via Genie SDK :contentReference[oaicite:4]{index=4}
