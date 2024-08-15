import argparse
import os
import re
from typing import Callable

import lxml.etree

NAMESPACE = "http://www.gribuser.ru/xml/fictionbook/2.0"
JUNK_WORDS = ["A", "AN", "THE", "AND", "OR", "И", "ИЛИ", "О"]


def main() -> None:
    args = parse_args()
    process(args.filename)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="FB2 file to rename")
    return parser.parse_args()


def process(filepath: str, verbose: bool = True) -> None:
    metadata = read_metadata(filepath)
    new_basename = construct_name(metadata)
    new_filepath = rename_file(filepath, new_basename)
    if verbose:
        print(f"{filepath} -> {new_filepath}")


def read_metadata(filepath: str) -> dict[str, str | None]:
    root = lxml.etree.parse(filepath).getroot()
    metadata = {
        "first-name": read_xpath(root, "//description/title-info/author/first-name").text,
        "last-name": read_xpath(root, "//description/title-info/author/last-name").text,
        "book-title": read_xpath(root, "//description/title-info/book-title").text,
    }

    sequence = read_xpath(root, "//description/title-info/sequence")
    if sequence is not None:
        metadata.update(
            {
                "sequence": sequence.attrib.get("name"),
                "number": sequence.attrib.get("number"),
            }
        )

    return metadata


def read_xpath(root: lxml.etree._Element, path: str) -> lxml.etree._Element:
    path = _map_split(path, "/", _add_namespace)
    elements = root.xpath(path, namespaces={"fb2": NAMESPACE})
    return elements[0]


def _map_split(text: str, splitter: str, func: Callable) -> str:
    return splitter.join(func(segment) for segment in text.split(splitter))


def _add_namespace(segment: str) -> str:
    if not segment or ":" in segment:
        return segment
    return f"fb2:{segment}"


def construct_name(metadata: dict[str, str | None]) -> str:
    author = " ".join(filter(None, [metadata.get("first-name"), metadata.get("last-name")]))
    title = metadata.get("book-title")
    sequence = None
    number = metadata.get("number")
    if number:
        sequence = metadata.get("sequence") or ""
        sequence = re.sub(r"\W", " ", sequence).strip().upper()
        sequence = "".join(
            word[0] for word in sequence.split() if word not in JUNK_WORDS
        ) + number.zfill(2)
    name = " - ".join(filter(None, [author, sequence, title]))
    return name.replace(":", "")


def rename_file(filepath: str, new_basename: str) -> str:
    dirname = os.path.dirname(filepath)
    extension = os.path.splitext(filepath)[1]
    new_filepath = os.path.join(dirname, f"{new_basename}{extension}")
    os.rename(filepath, new_filepath)
    return new_filepath


if __name__ == "__main__":
    main()
