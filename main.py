import uvicorn


def main() -> None:
    uvicorn.run("web.server:app", host="127.0.0.1", port=8741, reload=False)


if __name__ == "__main__":
    main()
