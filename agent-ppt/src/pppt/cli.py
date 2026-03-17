import argparse

from .exporter import JsonToPptxExporter


def main():
    parser = argparse.ArgumentParser(description="Export JSON presentation to PPTX (Open XML).")
    parser.add_argument("json_file", help="Path to input JSON file")
    parser.add_argument("-o", "--output", default="output.pptx", help="Output pptx path")
    args = parser.parse_args()

    JsonToPptxExporter.from_json_file(args.json_file, args.output)
    print(f"Done: {args.output}")


if __name__ == "__main__":
    main()
