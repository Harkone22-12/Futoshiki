import argparse
import json

from main import solve_payload


def _to_bool(raw):
    if isinstance(raw, bool):
        return raw
    text = str(raw).strip().lower()
    return text in {"1", "true", "yes", "y", "on"}


def parse_args():
    parser = argparse.ArgumentParser(description="Single benchmark case worker")
    parser.add_argument("--path", required=True)
    parser.add_argument("--algo", required=True)
    parser.add_argument("--heur", default="")
    parser.add_argument("--fc", default="0")
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        result = solve_payload(
            path=args.path,
            algo=args.algo,
            heur=args.heur,
            fc=_to_bool(args.fc),
        )
        packet = {
            "ok": True,
            "result": {
                "solved": bool(result.get("solved", False)),
                "elapsed": float(result.get("elapsed", 0.0)),
                "nodes": result.get("nodes", "N/A"),
                "peak_memory_mb": result.get("peak_memory_mb", ""),
                "note": str(result.get("note", "")).strip(),
            },
        }
        print(json.dumps(packet, ensure_ascii=True))
        return 0
    except Exception as ex:
        packet = {"ok": False, "error": str(ex)}
        print(json.dumps(packet, ensure_ascii=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
