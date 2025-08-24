# Setup

## Prerequisites

Before setting up Curato, ensure you have the following prerequisites installed and configured:

### **System Requirements**
- **Operating System**: Windows on Snapdragon (Snapdragon X Elite)
- **Architecture**: ARM64 (aarch64)
- **Memory**: Minimum 8GB RAM (16GB recommended)
- **Storage**: At least 10GB free space for models and dependencies

### **Required Software**
- **.NET SDK**: Version 7.0 or higher
  - Download from: https://dotnet.microsoft.com/en-us/download/dotnet/7.0
  - Verify installation: `dotnet --version`

- **Python**: Version 3.10.4 (exact version required)
  - Download from: http://python.org/downloads/release/python-3104/
  - Verify installation: `python --version`

- **Git**: Latest version
  - Download from: https://git-scm.com/
  - Verify installation: `git --version`

- **QAIRT SDK**: Version 2.34.2.250528164111_119506 (exact version required)
  - Download from: https://qpm.qualcomm.com/#/main/tools/details/Qualcomm_AI_Runtime_SDK
  - Extract to a known location (e.g., `C:\QAIRT_SDK`)

### **Environment Variables**
Set the following global environment variables:

```bash
# QAIRT SDK Root Path
QNN_SDK_ROOT=C:\QAIRT_SDK

# Python Path
PATH=%PATH%;C:\Users\<YourUsername>\AppData\Local\Programs\Python\Python310\

# Git Path
PATH=%PATH%;C:\Program Files\Git\cmd

# Pip Path
PATH=%PATH%;C:\Users\<YourUsername>\AppData\Local\Programs\Python\Python310\Scripts
```

### **API Access**
- **Qualcomm AI Hub**: Account with API token for model downloads
- **Kakao Map API**: API key for location services
- **Hugging Face**: Account for model access (if required)

---

Download QAIRT SDK https://qpm.qualcomm.com/#/main/tools/details/Qualcomm_AI_Runtime_SDK

Set global environment variable QNN_SDK_ROOT to root path of QAIRT SDK

Install Python 3.10.4 http://python.org/downloads/release/python-3104/

Set global environment variable path for python

```bash
C:\Users\<YourUsername>\AppData\Local\Programs\Python\Python310\
```

Install Git

Set global environment variable path for git

```bash
C:\Program Files\Git\cmd
```

Install pip

```bash
python -m pip install --upgrade pip
```

Set global environment variable path for pip

```bash
C:\Users\<YourUsername>\AppData\Local\Programs\Python\Python310\Scripts
```

Install ai_hub package

```bash
pip install qai_hub_models
```

Configure your API token: `qai-hub configure —api_token API_TOKEN`

Create Virtual Environment

```bash
python -m venv llm_on_genie_venv
```

Allow Script Execution

```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```

Activate a new Virtual Environment

```bash
.\llm_on_genie_venv\Scripts\Activate.ps1
```

Install the llama model from AI Hub Model

```bash
pip install -U "qai-hub-models[qwen2-5-7b-instruct]"
```

Acquire Genie Compatible QNN binaries from AI Hub

```bash
hf auth login
```

To generate the Llama assets, we will run a single command that performs the following steps:

1. Download model weights from Hugging Face. You will need to sign the Llama license if you haven’t already done so.
2. Upload models to AI Hub for compilation.
3. Download compiled context binaries. Note that there are multiple binaries as we have split up the model.

Make a directory to put in all deployable llama assets.

```bash
mkdir -p qwen_bundle
```

<aside>
💡

The export command below may take 4-6 hours. It takes an additional 1-2 hours on PyTorch versions earlier than 2.4.0. We recommend upgrading PyTorch first:

```bash
pip install torch==2.4.1
```

</aside>

```bash
python -m qai_hub_models.models.qwen2_5_7b_instruct.export --chipset qualcomm-snapdragon-x-elite --skip-inferencing --skip-profiling --output-dir qwen_bundle
```

Prepare Genie Configs

**Tokenizer**

To download the tokenizer, go to the source model's Hugging Face page and go to "Files and versions." You can find a Hugging Face link through the model card on [AI Hub](https://aihub.qualcomm.com/). This will take you to the Qualcomm Hugging Face page, which in turn will have a link to the source Hugging Face page. The file will be named `tokenizer.json` and should be downloaded to the `qwen_bundle` directory. The tokenizers are only hosted on the source Hugging Face page.

Genie Config

Check out the [AI Hub Apps repository](https://github.com/quic/ai-hub-apps) using Git:

```
git clone https://github.com/quic/ai-hub-apps.git
```

Now run (replacing `llama_v3_8b_instruct` with the desired model id):

```
cp ai-hub-apps/tutorials/llm_on_genie/configs/genie/qwen2_5_7b_instruct.json qwen_bundle/genie_config.json
```

For Windows laptops, please set `use-mmap` to `false`.

If you customized context length by adding `--context-length` to the export command, please open `genie_config.json` and modify the `"size"` option (under `"dialog"` -> `"context"`) to be consistent.

In `qwen_bundle/genie_config.json`, also ensure that the list of bin files in `ctx-bins` matches with the bin files under `qwen_bundle`. Genie will look for QNN binaries specified here.

**HTP Backend Config**

Copy the HTP config template:

```
cp ai-hub-apps/tutorials/llm_on_genie/configs/htp/htp_backend_ext_config.json.template qwen_bundle/htp_backend_ext_config.json
```

Edit `soc_model` and `dsp_arch` in `qwen_bundle/htp_backend_ext_config.json` depending on your target device (should be consistent with the `--chipset` you specified in the export command):

| **Generation** | **`soc_model`** | **`dsp_arch`** |
| --- | --- | --- |
| Snapdragon® Gen 2 | 43 | v73 |
| Snapdragon® Gen 3 | 57 | v75 |
| Snapdragon® 8 Elite | 69 | v79 |
| Snapdragon® X Elite | 60 | v73 |
| Snapdragon® X Plus | 60 | v73 |

**Collect & Finalize Genie Bundle**

When finished with the above steps, your bundle should look like this:

```
qwen_bundle/
   genie_config.json
   htp_backend_ext_config.json
   tokenizer.json
   <model_id>_part_1_of_N.bin
   ...
   <model_id>_part_N_of_N.bin

```

where <model_id> is the name of the model. This is the name of the json you copied from `configs/genie/<model_name>.json`.

**Run Genie On-Device via `genie-t2t-run`**

Please ensure that the QAIRT (or QNN) SDK version installed on the system is the same as the one used by AI Hub for generating context binaries. You can find the AI Hub QAIRT version in the compile job page as shown in the following screenshot:

![QAIRT version on AI Hub](https://github.com/quic/ai-hub-apps/raw/main/apps/windows/cpp/ChatApp/assets/images/ai-hub-qnn-version.png)

Having different QAIRT versions could result in runtime or load-time failures. ()

**Genie on Windows with Snapdragon® X**

Copy Genie's shared libraries and executable to our bundle. (Note you can skip this step if you used the powershell script to prepare your bundle.)

```powershell
Copy-Item "$env:QNN_SDK_ROOT/lib/hexagon-v73/unsigned/*" qwen_bundle
Copy-Item "$env:QNN_SDK_ROOT/lib/aarch64-windows-msvc/*" qwen_bundle
Copy-Item "$env:QNN_SDK_ROOT/bin/aarch64-windows-msvc/genie-t2t-run.exe" qwen_bundle
```

In Powershell, navigate to the bundle directory and run

```powershell
./genie-t2t-run.exe -c genie_config.json -p "<|im_start|>system\nYou are a helpful AI Assistant<|im_end|>\n\n<|im_start|>user\nWhat is France's capital?<|im_end|>\n\n<|im_start|>assistant\n"
```

Note that this prompt format is specific to Qwen 2.5.

After that, move both “qwen_bundle” into the curato directory.

Change [config.py](http://config.py) bundle path accordingly.
