from src.reolink.utils.CredentialHandler import CredentialHandler

credentials = CredentialHandler()

username, password, ip = credentials.load_credentials(1)
print(username, password, ip)
