"""Store a Binance Spot Testnet credential without echoing secret material."""

import argparse
from getpass import getpass

from dcabot.application.credential_boundary import CredentialMaterial
from dcabot.application.signed_request import ApiKeyType
from dcabot.application.windows_credential_provider import WindowsCredentialManagerProvider


def main() -> None:
    parser = argparse.ArgumentParser(description="Store a local Binance Spot Testnet credential.")
    parser.add_argument("credential_id", help="Local credential identity, for example testnet-readonly")
    args = parser.parse_args()
    provider = WindowsCredentialManagerProvider(key_type=ApiKeyType.HMAC)
    material = CredentialMaterial(
        credential_id=args.credential_id,
        api_key=getpass("Binance Testnet API key: "),
        key_type=ApiKeyType.HMAC,
        secret=getpass("Binance Testnet API secret: ").encode("utf-8"),
    )
    provider.put(material)
    print(f"Credential kaydedildi: {args.credential_id} (HMAC, redacted)")


if __name__ == "__main__":
    main()
