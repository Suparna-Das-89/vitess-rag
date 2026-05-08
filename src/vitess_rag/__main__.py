import argparse

from .agent import ask_hybrid_agent
from .chroma import get_or_create_collection, index_markdown_directory
from .embeddings import BlabladorEmbeddingFunction


def main() -> None:
    parser = argparse.ArgumentParser(prog="vitess-rag")
    subparsers = parser.add_subparsers(dest="command", required=True)

    index_parser = subparsers.add_parser(
        "index",
        help="Index Markdown files into Chroma.",
    )
    index_parser.add_argument("--input-dir", default="data")
    index_parser.add_argument("--persist-path", default="chroma_db")
    index_parser.add_argument("--collection", default="vitess_docs_blablador_v3")
    index_parser.add_argument("--jsonl", default="all_modules_chunks.jsonl")
    index_parser.add_argument("--no-recreate", action="store_true")

    ask_parser = subparsers.add_parser(
        "ask",
        help="Ask a question against an existing Chroma collection.",
    )
    ask_parser.add_argument("query")
    ask_parser.add_argument("--persist-path", default="chroma_db")
    ask_parser.add_argument("--collection", default="vitess_docs_blablador_v3")

    args = parser.parse_args()
    embedding_function = BlabladorEmbeddingFunction()

    if args.command == "index":
        collection, chunks = index_markdown_directory(
            input_dir=args.input_dir,
            persist_path=args.persist_path,
            collection_name=args.collection,
            embedding_function=embedding_function,
            output_jsonl=args.jsonl,
            recreate=not args.no_recreate,
        )

        print(f"Indexed chunks: {len(chunks)}")
        print(f"Collection count: {collection.count()}")

    elif args.command == "ask":
        collection = get_or_create_collection(
            persist_path=args.persist_path,
            collection_name=args.collection,
            embedding_function=embedding_function,
            recreate=False,
        )

        answer = ask_hybrid_agent(
            query=args.query,
            collection=collection,
        )

        print(answer)


if __name__ == "__main__":
    main()
