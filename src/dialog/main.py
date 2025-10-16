from src.dialog.dialog_loop import DialogLoop


def main() -> None:
    dlg = DialogLoop(use_gpu=False)
    dlg.start()


if __name__ == "__main__":
    main()
