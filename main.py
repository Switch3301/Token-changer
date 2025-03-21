import base64
import os
import json
import hashlib
import websocket
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import curl_cffi.requests as requests


class Main:
    def __init__(self, token: str) -> None:
        self.token = token
        self.sess = requests.Session(impersonate="chrome131") # change it to 124 if your using windows
        self.headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'authorization': self.token,
            'content-type': 'application/json',
            'origin': 'https://discord.com',
            'referer': 'https://discord.com/channels/@me',
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'x-debug-options': 'bugReporterEnabled',
            'x-discord-locale': 'en-US',
            'x-discord-timezone': 'Asia/Tokyo',
            'x-super-properties': 'eyJvcyI6IkxpbnV4IiwiYnJvd3NlciI6IkNocm9tZSIsImRldmljZSI6IiIsInN5c3RlbV9sb2NhbGUiOiJlbi1VUyIsImJyb3dzZXJfdXNlcl9hZ2VudCI6Ik1vemlsbGEvNS4wIChYMTE7IExpbnV4IHg4Nl82NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzEzMS4wLjAuMCBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiMTMxLjAuMC4wIiwib3NfdmVyc2lvbiI6IiIsInJlZmVycmVyIjoiIiwicmVmZXJyaW5nX2RvbWFpbiI6IiIsInJlZmVycmVyX2N1cnJlbnQiOiIiLCJyZWZlcnJpbmdfZG9tYWluX2N1cnJlbnQiOiIiLCJyZWxlYXNlX2NoYW5uZWwiOiJzdGFibGUiLCJjbGllbnRfYnVpbGRfbnVtYmVyIjozODAyMTMsImNsaWVudF9ldmVudF9zb3VyY2UiOm51bGx9'
        }
        self.sess.headers.update(self.headers)
        self.ws_url = "wss://remote-auth-gateway.discord.gg/?v=2"
    
    def create_kp(self) -> tuple:
        priv = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
        return priv.public_key(), priv
    
    def encode_pk(self, pub) -> str:
        return base64.b64encode(pub.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )).decode('utf-8')
    
    def proc_nonce(self, nonce_data: str, priv) -> str:
        data = json.loads(nonce_data)
        enc_nonce = base64.b64decode(data["encrypted_nonce"])
        
        dec_nonce = priv.decrypt(
            enc_nonce,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return json.dumps({
            "op": "nonce_proof",
            "proof": base64.urlsafe_b64encode(hashlib.sha256(dec_nonce).digest()).rstrip(b"=").decode(),
        })
    
    def decrypt(self, enc_data: str, priv) -> bytes:
        if not enc_data:
            return None
        
        payload = base64.b64decode(enc_data)
        return priv.decrypt(
            payload,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
    
    def handshake(self, fp: str) -> None:
        r = self.sess.post(
            "https://discord.com/api/v9/users/@me/remote-auth", 
            json={'fingerprint': fp}
        ).json()
        
        token = r.get('handshake_token')
        if token:
            self.sess.post(
                "https://discord.com/api/v9/users/@me/remote-auth/finish", 
                json={'handshake_token': token}
            )
    
    def logout(self, token: str) -> bool:
        hdrs = self.headers.copy()
        hdrs['authorization'] = token
        self.sess.headers.update(hdrs)
        
        r = self.sess.post(
            'https://discord.com/api/v9/auth/logout',
            json={'provider': None, 'voip_provider': None}
        )
        return r.status_code == 204
    
    def clone(self) -> str:
        try:
            ws = websocket.create_connection(
                self.ws_url,
                header=[
                    f"Authorization: {self.token}",
                    "Origin: https://discord.com"
                ]
            )
            
            ws.recv()
            
            pub, priv = self.create_kp()
            enc_key = self.encode_pk(pub)
            
            ws.send(json.dumps({"op": "init", "encoded_public_key": enc_key}))
            
            nonce = ws.recv()
            proof = self.proc_nonce(nonce, priv)
            ws.send(proof)
            
            print("Processing...")
            fp_data = json.loads(ws.recv())
            fp = fp_data.get("fingerprint")
            if not fp:
                return None
            
            self.handshake(fp)
            
            user_data = json.loads(ws.recv())
            enc_user = user_data.get("encrypted_user_payload")
            if enc_user:
                self.decrypt(enc_user, priv)
            
            ticket_data = json.loads(ws.recv())
            ticket = ticket_data.get("ticket")
            if not ticket:
                return None
            
            login_r = self.sess.post(
                "https://discord.com/api/v9/users/@me/remote-auth/login", 
                json={"ticket": ticket}
            )
            
            r_data = login_r.json()
            enc_token = r_data.get("encrypted_token")
            if not enc_token:
                return None
            
            ws.close()
            
            new_token = self.decrypt(enc_token, priv)
            if not new_token:
                return None
                
            return new_token.decode('utf-8')
            
        except Exception as e:
            print(f"Error: {e}")
            return None


def run(token: str = None) -> str:
    token = token or input("Token: ")
    dc = Main(token)
    new_token = dc.clone()
    
    if new_token and dc.logout(token):
        print(f"Changed: {new_token}")
        return new_token
        
    print("× Failed")
    return None


if __name__ == "__main__":
    run()