import hashlib

from Crypto.Cipher import AES
from Crypto import Random

PKCS5_SALT_LEN = 8
AES_BLOCKSIZE = AES.block_size
AES_KEYLEN = 32


def generate_bytes_openssl_md5(password, salt, num_bytes):
    lastBlock = b""
    totalData = b""
    while len(totalData) < num_bytes:
        md5 = hashlib.md5()
        md5.update(lastBlock + password + salt)
        lastBlock = md5.digest()
        totalData = totalData + lastBlock
    return totalData


def generate_openssl_key_data(password: str):
    salt = Random.new().read(PKCS5_SALT_LEN)
    pw = password.encode("utf-8")
    key_material = generate_bytes_openssl_md5(pw, salt, AES_KEYLEN + AES_BLOCKSIZE)
    key = key_material[0:AES_KEYLEN]
    iv = key_material[AES_KEYLEN:(AES_KEYLEN+AES_BLOCKSIZE)]
    return key, iv, salt


def calculate_padding(plaintext_len):
    last_block_size = plaintext_len % AES_BLOCKSIZE
    # if out text is exactly a multiple of block length, a block with just padding is added
    if last_block_size == AES_BLOCKSIZE:
        last_block_size = 0
    return bytes([AES_BLOCKSIZE - last_block_size]) * (AES_BLOCKSIZE - (plaintext_len % AES_BLOCKSIZE))


def encrypt_data_for_gammel_grandstream(password: str, data: bytes):
    key, iv, salt = generate_openssl_key_data(password)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = data + calculate_padding(len(data))
    ciphertext = cipher.encrypt(plaintext)
    openssl_output = b"Salted__" + salt + ciphertext
    return openssl_output



