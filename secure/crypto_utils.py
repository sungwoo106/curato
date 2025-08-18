"""
Cryptographic Utilities for API Key Security

This module provides secure handling of sensitive API keys using asymmetric
cryptography. It encrypts and decrypts the Kakao Map API key to prevent
exposure of sensitive credentials in the source code.

Security Features:
- Asymmetric encryption using RSA keys
- OAEP padding for secure encryption
- SHA256 hashing for message digest
- Private key-based decryption only

The module ensures that API keys are never stored in plain text and
can only be decrypted by authorized parties with access to the private key.

Note: This requires the cryptography library and properly configured
RSA key pairs for secure operation.
"""

# Import required cryptographic primitives
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

def get_kakao_map_api_key(
    encrypted_key_path: str = "secure/encrypted_api_key.bin",
    private_key_path: str = "secure/private_key_rest.pem",
) -> str:
    """
    Decrypt the encrypted Kakao Map API key using the provided private key.
    
    This function securely retrieves the Kakao Map API key by decrypting
    an encrypted file using asymmetric cryptography. The API key is never
    stored in plain text, ensuring security even if the source code is
    compromised.
    
    The decryption process uses:
    - RSA asymmetric encryption with OAEP padding
    - SHA256 hashing for secure message digest
    - Private key-based decryption (only authorized parties can decrypt)
    
    Args:
        encrypted_key_path (str): Path to the file containing the encrypted API key.
                                  Default: "secure/encrypted_api_key.bin"
        private_key_path (str): Path to the file containing the private key used
                                for decryption. Default: "secure/private_key_rest.pem"
    
    Returns:
        str: Decrypted Kakao Map API key as a string, ready for use in API calls.
    
    Raises:
        FileNotFoundError: If the encrypted key file or private key file is not found
        ValueError: If the private key is invalid or corrupted
        cryptography.exceptions.InvalidKey: If the private key cannot be loaded
        cryptography.exceptions.DecryptionError: If decryption fails
    
    Security Notes:
        - The private key should be kept secure and never shared
        - The encrypted key file can be safely committed to version control
        - Decryption only works with the correct private key
        - API keys are decrypted in memory only when needed
    
    Example:
        >>> api_key = get_kakao_map_api_key()
        >>> print(f"API Key: {api_key[:10]}...")
        API Key: KakaoAK_abc...
    
    Dependencies:
        - cryptography library
        - Valid RSA private key file
        - Encrypted API key file
    """
    # Load the encrypted API key from the binary file
    # The encrypted key is stored as raw bytes for security
    with open(encrypted_key_path, "rb") as f:
        encrypted_key = f.read()

    # Load the private key from the PEM file
    # The private key is used to decrypt the API key
    # password=None indicates the private key is not password-protected
    with open(private_key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,  # No password protection on the private key
        )

    # Decrypt the API key using the private key
    # This reverses the encryption process to recover the original API key
    decrypted_key = private_key.decrypt(
        encrypted_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),  # Mask Generation Function for secure padding
            algorithm=hashes.SHA256(),                     # SHA256 hashing algorithm
            label=None                                     # No additional label for this encryption
        )
    )

    # Convert the decrypted bytes to a UTF-8 string
    # The API key is now ready for use in HTTP requests
    return decrypted_key.decode('utf-8')
