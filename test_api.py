"""Smoke-test the configured OpenRouter backend."""

from llm_client import call_online


def main() -> None:
    reply = call_online([{"role": "user", "content": "Say hello in one short sentence."}])
    if not reply:
        raise RuntimeError("OpenRouter returned an empty response.")
    print(reply)


if __name__ == "__main__":
    main()
