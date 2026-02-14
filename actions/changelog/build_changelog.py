#!/usr/bin/env python3
import argparse
import json

from changelog_config import load_changelog_config


def _pr_labels(pr):
    labels = pr.get("labels", [])
    if not isinstance(labels, list):
        return set()

    out = set()
    for label in labels:
        if isinstance(label, str):
            out.add(label)
        elif isinstance(label, dict) and label.get("name"):
            out.add(label["name"])
    return out


def _render_pr_line(pr):
    number = pr.get("number")
    title = (pr.get("title") or "").strip()
    url = pr.get("html_url") or ""
    if number and url:
        return f"- {title} [#{number}]({url})"
    if number:
        return f"- {title} #{number}"
    return f"- {title}"


def _apply_template(template, changes):
    return template.replace("$CHANGES", changes).replace("{{CHANGELOG}}", changes)


def load_prs(pr_info_path):
    with open(pr_info_path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)

    info = payload.get("pr_info", payload)
    prs = info.get("pull_requests", [])
    if not isinstance(prs, list):
        return []
    return prs


def build_changelog(prs, config):
    categories = config["categories"]
    exclude = config["exclude_labels"]

    grouped = {idx: [] for idx in range(len(categories))}
    misc = []
    included_prs = []

    for pr in prs:
        labels = _pr_labels(pr)
        if labels & exclude:
            continue

        line = _render_pr_line(pr)
        number = pr.get("number")
        if number is not None:
            included_prs.append(str(number))

        matched = False
        for idx, category in enumerate(categories):
            if labels & set(category["labels"]):
                grouped[idx].append(line)
                matched = True
                break

        if not matched:
            misc.append(line)

    sections = []
    for idx, category in enumerate(categories):
        lines = grouped[idx]
        if not lines:
            continue
        sections.append(f"{category['title']}\n")
        sections.extend(lines)
        sections.append("")

    if misc:
        sections.append("### Miscellaneous\n")
        sections.extend(misc)
        sections.append("")

    changes = "\n".join(sections).strip()
    changelog = _apply_template(config["template"], changes)

    return {
        "changes": changes,
        "changelog": changelog,
        "pull_requests": ",".join(included_prs),
    }


def to_line(result):
    lines = []
    if result.get("pull_requests") is not None:
        lines.append(f"pull-requests={result['pull_requests']}")

    # multiline outputs
    lines.append("changes<<EOF_CHANGELOG_CHANGES")
    lines.append(result.get("changes", ""))
    lines.append("EOF_CHANGELOG_CHANGES")

    lines.append("changelog<<EOF_CHANGELOG")
    lines.append(result.get("changelog", ""))
    lines.append("EOF_CHANGELOG")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Build changelog from pr_info JSON and changelog.yml")
    parser.add_argument("--config-path", required=True)
    parser.add_argument("--pr-info-path", required=True)
    parser.add_argument("--output-format", choices=["json", "line"], default="json")
    args = parser.parse_args()

    config = load_changelog_config(args.config_path)
    prs = load_prs(args.pr_info_path)
    result = build_changelog(prs, config)

    if args.output_format == "line":
        print(to_line(result))
    else:
        print(json.dumps(result))


if __name__ == "__main__":
    main()
