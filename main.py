import asyncio
from modules.deposit_to_gasp import start_deposit


def load_private_key_from_file(file_path):
    try:
        with open(file_path, 'r') as file:
            private_key = file.read().strip()
            if not private_key:
                raise ValueError("Private key file is empty")
            return private_key
    except FileNotFoundError:
        raise FileNotFoundError(f"Private key file '{file_path}' not found.")
    except Exception as e:
        raise RuntimeError(f"Error loading private key: {e}")


async def run_deposit(private_key, rpc_url):
    await start_deposit(private_key, rpc_url)


if __name__ == "__main__":
    private_key_file_path = "private_keys.txt"
    rpc_url = "https://holesky.drpc.org"
    private_key = load_private_key_from_file(private_key_file_path)

    try:
        asyncio.run(run_deposit(private_key, rpc_url))
    except RuntimeError as e:
        print(f"Runtime error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
