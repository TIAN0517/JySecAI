#!/usr/bin/env python3
import argparse
import datetime
import os
import pathlib
import shutil


CHANNEL = "vast-qwen38"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--api-key-file", required=True)
    args = parser.parse_args()

    config = pathlib.Path(args.config)
    api_key = pathlib.Path(args.api_key_file).read_text(encoding="utf-8").strip()
    if not api_key:
        raise SystemExit("API key file is empty")

    original = config.read_text(encoding="utf-8")
    lines = original.splitlines(keepends=True)
    ai_start = next(i for i, line in enumerate(lines) if line.rstrip() == "ai:")
    ai_end = next(
        (i for i in range(ai_start + 1, len(lines)) if lines[i].strip() and not lines[i].startswith((" ", "\t", "#"))),
        len(lines),
    )
    default_index = next(
        i for i in range(ai_start + 1, ai_end) if lines[i].startswith("  default_channel:")
    )
    newline = "\r\n" if lines[default_index].endswith("\r\n") else "\n"
    lines[default_index] = f"  default_channel: {CHANNEL}{newline}"

    channels_index = next(
        i for i in range(ai_start + 1, ai_end) if lines[i].rstrip() == "  channels:"
    )
    channel_start = next(
        (i for i in range(channels_index + 1, ai_end) if lines[i].rstrip() == f"    {CHANNEL}:"),
        None,
    )
    if channel_start is not None:
        channel_end = next(
            (
                i
                for i in range(channel_start + 1, ai_end)
                if lines[i].strip()
                and not lines[i].startswith("      ")
                and not lines[i].lstrip().startswith("#")
            ),
            ai_end,
        )
        del lines[channel_start:channel_end]

    block = [
        f"    {CHANNEL}:{newline}",
        f"      name: Qwen3.8 27B Uncensored GPU{newline}",
        f"      provider: openai_compatible{newline}",
        f"      base_url: http://127.0.0.1:10300/v1{newline}",
        f"      api_key: \"{api_key}\"{newline}",
        f"      model: Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-Q8_K_P.gguf{newline}",
        f"      max_total_tokens: 32768{newline}",
        f"      max_completion_tokens: 8192{newline}",
        f"      reasoning:{newline}",
        f"        mode: auto{newline}",
        f"        allow_client_reasoning: true{newline}",
        f"        profile: auto{newline}",
    ]
    lines[channels_index + 1:channels_index + 1] = block

    updated = "".join(lines)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = config.with_name(f"{config.name}.bak-qwen38-{stamp}")
    shutil.copy2(config, backup)
    temporary = config.with_name(f".{config.name}.qwen38.tmp")
    temporary.write_text(updated, encoding="utf-8")
    os.chmod(temporary, config.stat().st_mode)
    os.replace(temporary, config)
    print(f"configured {config}; backup {backup}")


if __name__ == "__main__":
    main()
