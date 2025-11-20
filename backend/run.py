import uvicorn


def main() -> None:
    """Run the FastAPI development server with automatic reload."""
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
