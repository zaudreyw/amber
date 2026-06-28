#!/usr/bin/env python3
"""Probe LLM endpoints to triage harness slowness.

Sends a tiny prompt at one or more (provider, model) combinations and prints
latency, output, and any error/retry information. Useful for distinguishing
"this provider is throttling us" from "this model is slow" when the GEOS eval
harness stalls.

Examples
--------

    # Sanity check: minimax via OpenRouter (our historical workhorse)
    python scripts/api_probe.py --target openrouter:minimax/minimax-m2.7

    # The new fast DeepSeek model on multiple providers — direct vs OpenRouter
    python scripts/api_probe.py \
      --target deepseek:deepseek-v4-flash \
      --target openrouter:deepseek/deepseek-v4-flash \
      --runs 3

    # Compare latencies across many models
    python scripts/api_probe.py \
      --target openrouter:minimax/minimax-m2.7 \
      --target openrouter:deepseek/deepseek-v4-flash \
      --target openrouter:google/gemma-4-31b-it \
      --target openai:gpt-5 \
      --runs 2

Targets are written as ``<provider>:<model>``. Supported providers:

  - ``openrouter`` — uses ``OPENROUTER_API_KEY`` and base URL
    ``https://openrouter.ai/api/v1``.
  - ``deepseek`` — uses ``DEEPSEEK_API_KEY`` and base URL
    ``https://api.deepseek.com``.
  - ``openai`` — uses ``OPENAI_API_KEY`` and the SDK default base URL.
  - ``anthropic`` — uses ``ANTHROPIC_API_KEY`` (or falls back to
    ``ANTHROPIC_AUTH_TOKEN``); requires the ``anthropic`` SDK.

The script auto-loads ``.env`` from the repo root if present, so it works
with the project's existing key layout.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv() -> None:
    env_path = REPO_ROOT / ".env"
    if not env_path.is_file():
        return
    for raw in env_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        os.environ.setdefault(key, val)


@dataclass
class ProbeResult:
    target: str
    run_index: int
    latency_seconds: float | None
    ok: bool
    error_kind: str | None = None
    error_detail: str | None = None
    output_text: str | None = None
    usage: dict[str, Any] | None = None
    raw_meta: dict[str, Any] = field(default_factory=dict)


def _print_result(r: ProbeResult, *, show_text: bool, max_text: int) -> None:
    head = f"[{r.target}#{r.run_index}]"
    if r.ok:
        lat = f"{r.latency_seconds:.2f}s" if r.latency_seconds is not None else "?"
        usage = ""
        if r.usage:
            it = r.usage.get("prompt_tokens") or r.usage.get("input_tokens")
            ot = r.usage.get("completion_tokens") or r.usage.get("output_tokens")
            if it is not None and ot is not None:
                usage = f"  in={it} out={ot}"
        print(f"{head} OK  {lat}{usage}")
        if show_text and r.output_text:
            txt = r.output_text.strip().replace("\n", " ")
            if len(txt) > max_text:
                txt = txt[:max_text] + "..."
            print(f"{head}  -> {txt!r}")
    else:
        lat = f"{r.latency_seconds:.2f}s" if r.latency_seconds is not None else "?"
        print(f"{head} FAIL {lat}  kind={r.error_kind}")
        if r.error_detail:
            detail = r.error_detail
            if len(detail) > max_text * 4:
                detail = detail[: max_text * 4] + "..."
            print(f"{head}  detail: {detail}")


def _classify_error(exc: BaseException) -> str:
    name = type(exc).__name__
    text = repr(exc).lower()
    if "rate" in text or "429" in text:
        return "rate_limit"
    if "timeout" in text or "timed out" in text:
        return "timeout"
    if "auth" in text or "401" in text or "permission" in text:
        return "auth"
    if "402" in text or "credit" in text or "quota" in text:
        return "quota"
    if "connection" in text or "network" in text or "dns" in text or "ssl" in text:
        return "network"
    if "503" in text or "502" in text or "504" in text or "unavailable" in text:
        return "upstream_unavailable"
    if "404" in text or "not_found" in text or "model_not_found" in text:
        return "unknown_model"
    return name


def _build_openai_compatible_client(
    base_url: str | None,
    api_key: str,
):
    from openai import OpenAI  # type: ignore

    return OpenAI(base_url=base_url, api_key=api_key) if base_url else OpenAI(api_key=api_key)


def _probe_openai_chat(
    *,
    base_url: str | None,
    api_key: str,
    model: str,
    prompt: str,
    request_timeout: float,
    extra_body: dict[str, Any] | None = None,
) -> ProbeResult:
    target = f"{base_url or 'openai-default'}::{model}"
    started = time.time()
    try:
        client = _build_openai_compatible_client(base_url, api_key)
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "timeout": request_timeout,
        }
        if extra_body:
            kwargs["extra_body"] = extra_body
        resp = client.chat.completions.create(**kwargs)
        latency = time.time() - started
        text = (resp.choices[0].message.content or "").strip() if resp.choices else ""
        usage = None
        if resp.usage is not None:
            usage = {
                "prompt_tokens": getattr(resp.usage, "prompt_tokens", None),
                "completion_tokens": getattr(resp.usage, "completion_tokens", None),
                "total_tokens": getattr(resp.usage, "total_tokens", None),
            }
        return ProbeResult(
            target=target,
            run_index=0,
            latency_seconds=latency,
            ok=True,
            output_text=text,
            usage=usage,
            raw_meta={"id": getattr(resp, "id", None), "model": getattr(resp, "model", None)},
        )
    except BaseException as exc:  # noqa: BLE001 — probe wants to capture everything
        return ProbeResult(
            target=target,
            run_index=0,
            latency_seconds=time.time() - started,
            ok=False,
            error_kind=_classify_error(exc),
            error_detail=repr(exc),
        )


def _probe_anthropic_messages(
    *,
    api_key: str,
    model: str,
    prompt: str,
    request_timeout: float,
) -> ProbeResult:
    target = f"anthropic-direct::{model}"
    started = time.time()
    try:
        from anthropic import Anthropic  # type: ignore
    except ImportError as exc:
        return ProbeResult(
            target=target,
            run_index=0,
            latency_seconds=0.0,
            ok=False,
            error_kind="missing_sdk",
            error_detail=f"{exc}; install with `pip install anthropic`",
        )
    try:
        client = Anthropic(api_key=api_key, timeout=request_timeout)
        resp = client.messages.create(
            model=model,
            max_tokens=128,
            system="You are a helpful assistant.",
            messages=[{"role": "user", "content": prompt}],
        )
        latency = time.time() - started
        text = ""
        for block in resp.content:
            if getattr(block, "type", None) == "text":
                text += getattr(block, "text", "")
        usage = None
        if getattr(resp, "usage", None) is not None:
            usage = {
                "input_tokens": resp.usage.input_tokens,
                "output_tokens": resp.usage.output_tokens,
            }
        return ProbeResult(
            target=target,
            run_index=0,
            latency_seconds=latency,
            ok=True,
            output_text=text.strip(),
            usage=usage,
            raw_meta={"id": getattr(resp, "id", None), "model": getattr(resp, "model", None)},
        )
    except BaseException as exc:  # noqa: BLE001
        return ProbeResult(
            target=target,
            run_index=0,
            latency_seconds=time.time() - started,
            ok=False,
            error_kind=_classify_error(exc),
            error_detail=repr(exc),
        )


PROVIDER_CONFIG = {
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "key_env": "OPENROUTER_API_KEY",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "key_env": "DEEPSEEK_API_KEY",
    },
    "openai": {
        "base_url": None,  # SDK default
        "key_env": "OPENAI_API_KEY",
    },
}


def _parse_target(target: str) -> tuple[str, str]:
    if ":" not in target:
        raise SystemExit(f"target must be '<provider>:<model>', got {target!r}")
    provider, model = target.split(":", 1)
    return provider.strip().lower(), model.strip()


def _resolve_anthropic_key() -> str | None:
    return os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")


def run_target(
    *,
    target: str,
    runs: int,
    prompt: str,
    request_timeout: float,
    extra_body: dict[str, Any] | None = None,
) -> list[ProbeResult]:
    provider, model = _parse_target(target)
    results: list[ProbeResult] = []
    for i in range(1, runs + 1):
        if provider == "anthropic":
            api_key = _resolve_anthropic_key()
            if not api_key:
                results.append(
                    ProbeResult(
                        target=target,
                        run_index=i,
                        latency_seconds=0.0,
                        ok=False,
                        error_kind="missing_key",
                        error_detail="set ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN",
                    )
                )
                continue
            r = _probe_anthropic_messages(
                api_key=api_key,
                model=model,
                prompt=prompt,
                request_timeout=request_timeout,
            )
        elif provider in PROVIDER_CONFIG:
            cfg = PROVIDER_CONFIG[provider]
            api_key = os.environ.get(cfg["key_env"])
            if not api_key:
                results.append(
                    ProbeResult(
                        target=target,
                        run_index=i,
                        latency_seconds=0.0,
                        ok=False,
                        error_kind="missing_key",
                        error_detail=f"set {cfg['key_env']}",
                    )
                )
                continue
            r = _probe_openai_chat(
                base_url=cfg["base_url"],
                api_key=api_key,
                model=model,
                prompt=prompt,
                request_timeout=request_timeout,
                extra_body=extra_body,
            )
        else:
            results.append(
                ProbeResult(
                    target=target,
                    run_index=i,
                    latency_seconds=0.0,
                    ok=False,
                    error_kind="unknown_provider",
                    error_detail=f"provider {provider!r} not supported. "
                    f"Use one of: openrouter, deepseek, openai, anthropic.",
                )
            )
            continue
        r.target = target
        r.run_index = i
        results.append(r)
    return results


def _summarize(results: Iterable[ProbeResult]) -> dict[str, dict[str, Any]]:
    by_target: dict[str, list[ProbeResult]] = {}
    for r in results:
        by_target.setdefault(r.target, []).append(r)
    summary: dict[str, dict[str, Any]] = {}
    for target, rs in by_target.items():
        ok_lat = [r.latency_seconds for r in rs if r.ok and r.latency_seconds is not None]
        errs = [r for r in rs if not r.ok]
        entry: dict[str, Any] = {
            "n_runs": len(rs),
            "n_ok": len(ok_lat),
            "n_fail": len(errs),
        }
        if ok_lat:
            entry["lat_min_s"] = round(min(ok_lat), 3)
            entry["lat_mean_s"] = round(statistics.mean(ok_lat), 3)
            entry["lat_max_s"] = round(max(ok_lat), 3)
        if errs:
            entry["error_kinds"] = sorted({e.error_kind or "?" for e in errs})
        summary[target] = entry
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--target",
        action="append",
        required=True,
        help="<provider>:<model>. Repeatable. Providers: openrouter, deepseek, openai, anthropic.",
    )
    parser.add_argument(
        "--prompt",
        default="What is the capital of Japan? Answer in one word.",
        help="User message to send (default: a tiny capital-of-Japan probe).",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="Number of sequential probes per target (default: 1).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="Per-request timeout in seconds (default: 60).",
    )
    parser.add_argument(
        "--reasoning",
        action="store_true",
        help="Send `extra_body={'thinking': {'type':'enabled'}}` plus reasoning_effort='high'. "
             "Useful for DeepSeek/OpenAI thinking-capable models.",
    )
    parser.add_argument(
        "--quiet-text",
        action="store_true",
        help="Don't print model output text, only latency/usage/errors.",
    )
    parser.add_argument(
        "--max-text",
        type=int,
        default=200,
        help="Max characters of model output to print per run (default: 200).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a JSON summary at the end.",
    )
    args = parser.parse_args()

    _load_dotenv()

    extra_body: dict[str, Any] | None = None
    if args.reasoning:
        extra_body = {
            "thinking": {"type": "enabled"},
            "reasoning_effort": "high",
        }

    all_results: list[ProbeResult] = []
    for target in args.target:
        rs = run_target(
            target=target,
            runs=args.runs,
            prompt=args.prompt,
            request_timeout=args.timeout,
            extra_body=extra_body,
        )
        for r in rs:
            _print_result(r, show_text=not args.quiet_text, max_text=args.max_text)
            sys.stdout.flush()
            all_results.append(r)

    summary = _summarize(all_results)
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print()
        print("=== Summary ===")
        for target, entry in summary.items():
            line = f"  {target}: {entry['n_ok']}/{entry['n_runs']} OK"
            if "lat_mean_s" in entry:
                line += f", lat min/mean/max = {entry['lat_min_s']}/{entry['lat_mean_s']}/{entry['lat_max_s']}s"
            if entry["n_fail"]:
                line += f", failures: {entry.get('error_kinds')}"
            print(line)


if __name__ == "__main__":
    main()
