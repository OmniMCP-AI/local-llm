# Two-machine image pilot

The [planned comparison](plan.json) covers one Apple M4 using Metal and one GeForce RTX 4090 using CUDA. On November 21, 2026, the pinned workflow produced a warmup PNG and all five repeat PNGs in a private exploratory run on the 24 GiB M4. The host had background CPU and GPU activity and reached critical memory pressure during the run. A quiet-host capture and rights-cleared public evidence are pending. The private PNGs and blind review packet are ready for review. No authorized RTX 4090 host or operator-run evidence was available.

From `production`, build the planned public report into a new directory.

```sh
python3 -B -m fastest_image build /path/to/image-pilot-v1
```

The bundle has Markdown, static HTML, typed JSON, the exact API workflow, both dependency locks and their SHA-256 manifest. Keep the files together when serving the directory. Each build takes at most one reviewed record per planned machine. A correction or withdrawal requires replacing or removing the affected published bundle.

## Pin the workflow, weights and runtime

Use the [exact API graph](workflow.json) and [fixed protocol and acceptance rubric](plan.json). The graph draws one unbranded cobalt blue ceramic mug at 512 × 512 with one Euler ancestral step, the SD Turbo schedule, CFG 1 and denoise 1. It uses only the pinned ComfyUI core nodes and the single SDXL Turbo fp16 safetensors checkpoint, including both text encoders and the VAE. The workflow and wheel file digests appear in the plan and public manifest.

Use ComfyUI v0.3.28 at commit `a14c2fc3565277dfe8ab0ecb22a86c1d0a1f72cf`. A fresh Python 3.11 virtual environment is required. Install the appropriate wheel lock with hash verification. The MPS lock targets arm64 macOS 14 or later and PyTorch 2.6.0. The CUDA lock targets x86-64 Linux with glibc 2.28 or later, a driver supporting CUDA 12.4, and the PyTorch 2.6.0 CUDA 12.4 build. [Pinned ComfyUI source](https://github.com/Comfy-Org/ComfyUI/tree/a14c2fc3565277dfe8ab0ecb22a86c1d0a1f72cf)

```sh
python3.11 -m venv /path/to/image-pilot-venv
/path/to/image-pilot-venv/bin/python -m pip install --require-hashes --only-binary=:all: \
  -r /path/to/local-llm/production/fastest_image/requirements-mps.txt
```

On Linux, use `requirements-cuda.txt`. Each lock selects exact CPython 3.11 wheels from PyPI or PyTorch’s CUDA 12.4 wheel index. The source requirement list comes from the pinned ComfyUI commit. The lock also includes the local WebSocket capture client. Record the exact Python patch version, OS, driver and machine in the private provenance.

Place the official `sd_xl_turbo_1.0_fp16.safetensors` file in the checkout’s `models/checkpoints/` directory. Verify all 6,938,081,905 bytes have SHA-256 `e869ac7d6942cb327d68d5ed83a40447aadf20e0c3358d98b2cc9e270db0da26`. Treat the pinned non-commercial checkpoint terms as an execution input. Review any applicable rights before running commercially, redistributing weights or publicly releasing an output image. The reference report shares metadata, reviewed attempt records and image digests. [Official checkpoint and hash](https://huggingface.co/stabilityai/sdxl-turbo/blob/cf0e5cbf9cb1ce0f632875ea8e1b996a9df869d8/sd_xl_turbo_1.0_fp16.safetensors) · [Pinned checkpoint terms](https://huggingface.co/stabilityai/sdxl-turbo/blob/cf0e5cbf9cb1ce0f632875ea8e1b996a9df869d8/LICENSE.TXT)

## Capture one run on each available machine

Start a fresh, dedicated local ComfyUI process from the pinned checkout in a foreground terminal. Retain stdout and stderr privately. Verify that the process owns the loopback listener, that the queue is empty and that the pinned checkpoint is available. Check the startup and run records for the actual backend, active GPU and effective placement. Record baseline CPU and GPU activity and memory pressure to establish whether the host was quiet. On the CUDA host, select the RTX 4090 with `CUDA_VISIBLE_DEVICES` before startup.

```sh
/path/to/image-pilot-venv/bin/python main.py --listen 127.0.0.1 --port 8188 \
  --disable-all-custom-nodes --cache-classic --fp16-unet --fp32-vae --fp32-text-enc --preview-method none
```

From `production`, capture into a new private directory using the same environment.

```sh
/path/to/image-pilot-venv/bin/python -B -m fastest_image.capture /path/to/private-run
```

Capture queues the fixed warmup seed 731000 and then the five repeats 731001–731005. Each repeat changes only the sampler seed. It measures from just before local `POST /prompt` to the end of the local PNG read or terminal failure, with monotonic offsets for sampler start, decode start, save start and execution completion. The last phase covers PNG retrieval. The warmup stays in the ledger for audit and is excluded from the comparison. The client stops queueing after a 180-second timeout or unsuccessful warmup and preserves the observed prefix. Keep the attempt JSON, private PNGs and server logs. Stop the dedicated server with Ctrl+C when the run ends.

## Retain private timing

Import a sealed private capture packet into PostgreSQL with the [image-pilot intake command](../fastest_intake/README.md#import-private-image-pilot-timing). Its attempt rows preserve the warmup, repeats, failures and timing offsets while blind scoring and publication review are pending.

## Review and publish

Use [the synthetic ledger](../fixtures/synthetic-image-pilot.json) as a field guide. Copy the capture’s attempt list to `attempts`, including failed requests and their observed phase endpoints. Set `kind` to `measured` for a verified run that follows the pinned protocol. Supply the exact runtime, workflow, checkpoint and lock digests, runtime flags and hardware details. Link to a versioned public evidence record over HTTPS and retain the underlying run privately. Record a public-release allow decision covering the published fields. Use reviewer pseudonyms and rights-cleared notes.

Give the reviewer each retrieved repeat PNG under an opaque ID along with the exact prompt. Hide machine and timing details. If ComfyUI embeds workflow or seed metadata, use a review copy with that metadata removed and the decoded pixels unchanged. Retain the original capture and the ID mapping privately. Enter the four boolean scores and a note under the attempt’s `review`, or leave it `null` while pending. A repeat is accepted when all four criteria pass. Completion time is the median of successful repeats. Seconds per accepted image divides the sum of all five repeat times, including failed and rejected attempts, by the accepted count. The rate requires all five attempts, completed reviews of the retrieved images and at least one acceptance. The report retains missing metrics and partial results.

```sh
python3 -B -m fastest_image build /path/to/image-pilot-v2 \
  --record reviewed-m4.json --record reviewed-rtx4090.json
```

Omit the `--record` entry for an unavailable machine. Use explicit demo mode for a synthetic rehearsal.

```sh
python3 -B -m fastest_image build /path/to/image-pilot-demo \
  --demo --record fixtures/synthetic-image-pilot.json
```
