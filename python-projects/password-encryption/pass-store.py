from cryptography.fernet import Fernet
import os
import getpass

KEY_FILE = 'secret.key'
CREDENTIALS_FILE = 'credentials.txt'


def generate_key():
    """Generate and save a key if not already present."""
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, 'wb') as f:
            f.write(key)


def load_key():
    """Load the encryption key."""
    with open(KEY_FILE, 'rb') as f:
        return f.read()


def encrypt_password(password, key):
    """Encrypt the password."""
    f = Fernet(key)
    return f.encrypt(password.encode())


def decrypt_password(encrypted_password, key):
    """Decrypt the password."""
    f = Fernet(key)
    return f.decrypt(encrypted_password).decode()


def user_exists(username):
    """Check if a username already exists in the file."""
    if not os.path.exists(CREDENTIALS_FILE):
        return False
    with open(CREDENTIALS_FILE, 'r') as f:
        for line in f:
            stored_username, _ = line.strip().split(":")
            if stored_username == username:
                return True
    return False


def register():
    username = input("Register - Enter username: ").strip()
    if user_exists(username):
        print("❌ Username already exists. Please try another.")
        return

    password = getpass.getpass("Register - Enter password: ")
    key = load_key()
    encrypted_password = encrypt_password(password, key)

    with open(CREDENTIALS_FILE, 'a') as f:
        f.write(f"{username}:{encrypted_password.decode()}\n")

    print("✅ Registration successful.\n")


def login():
    username_input = input("Login - Enter username: ").strip()
    password_input = getpass.getpass("Login - Enter password: ")

    key = load_key()

    if not os.path.exists(CREDENTIALS_FILE):
        print("❌ No users found. Please register first.")
        return

    with open(CREDENTIALS_FILE, 'r') as f:
        for line in f:
            stored_username, encrypted_password = line.strip().split(":")
            if stored_username == username_input:
                try:
                    decrypted_password = decrypt_password(encrypted_password.encode(), key)
                    if decrypted_password == password_input:
                        print("✅ Login successful!")
                    else:
                        print("❌ Incorrect password.")
                    return
                except Exception:
                    print("❌ Error decrypting password. Possible data corruption.")
                    return

    print("❌ Username not found.")


def main():
    generate_key()
    while True:
        print("\n1. Register")
        print("2. Login")
        print("3. Exit")
        choice = input("Select an option: ")

        if choice == '1':
            register()
        elif choice == '2':
            login()
        elif choice == '3':
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
