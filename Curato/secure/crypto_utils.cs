using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;

namespace secure
{
    public static class crypto_utils
    {
        public static string get_kakao_map_api_key(string encryptedKeyPath = "secure/encrypted_api_key.bin",
                                                   string privateKeyPath = "secure/private_key.pem")
        {
            byte[] encryptedKey = File.ReadAllBytes(encryptedKeyPath);
            string privateKeyPem = File.ReadAllText(privateKeyPath);
            using RSA rsa = RSA.Create();
            rsa.ImportFromPem(privateKeyPem.ToCharArray());
            byte[] decrypted = rsa.Decrypt(encryptedKey, RSAEncryptionPadding.OaepSHA256);
            return Encoding.UTF8.GetString(decrypted);
        }
    }
}