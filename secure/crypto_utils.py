# Encrypts and decrypts API keys using a symmetric key.
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

def get_kakao_map_api_key(
    encrypted_key_path: str = "secure/encrypted_api_key.bin",
    private_key_path: str = "secure/private_key_rest.pem",
) -> str:
    """
    Decrypts the encrypted Kakao Map API key using the provided private key.
    @param encrypted_key_path: Path to the file containing the encrypted API key.
    @param private_key_path: Path to the file containing the private key used for decryption
    @return: Decrypted Kakao Map API key as a string.
    """

    # Load the encrypted API key
    with open(encrypted_key_path, "rb") as f:
        encrypted_key = f.read()

    # Load the private key
    with open(private_key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
        )

    # Decrypt the API key
    decrypted_key = private_key.decrypt(
        encrypted_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()), # Mask Generation Function allows for secure padding
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    return decrypted_key.decode('utf-8')
