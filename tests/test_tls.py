#!/usr/bin/env python3
"""TLS integration checks. Requires Python cryptography, a JDK and OpenSSL.
Use --live for GitHub checks with an unrelated simulated system trust store.
"""
import datetime,http.server,json,pathlib,ssl,subprocess,tempfile,threading,sys
from cryptography import x509
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
root=pathlib.Path(__file__).resolve().parents[1]
run=lambda args:subprocess.run([str(a) for a in args],check=True)
now=datetime.datetime.now(datetime.timezone.utc)
def cert(subject,key,issuer,signer,ca=False,expired=False,host=None):
    b=x509.CertificateBuilder().subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,subject)])).issuer_name(issuer).public_key(key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now-datetime.timedelta(days=2)).not_valid_after(now+datetime.timedelta(days=-1 if expired else 10)).add_extension(x509.BasicConstraints(ca=ca,path_length=None),critical=True)
    if host:b=b.add_extension(x509.SubjectAlternativeName([x509.DNSName(host)]),critical=False)
    return b.sign(signer,hashes.SHA256())
class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):self.send_response(200);self.end_headers();self.wfile.write(b'OK')
    def log_message(self,*args):pass
with tempfile.TemporaryDirectory(prefix='repoman-tls-') as folder:
    work=pathlib.Path(folder);servers=[]
    try:
        run(['javac','--release','8','-d',work,*[root/'src/dev/nemesiscatalog'/p for p in ['TlsTrust.java','Network.java','Policy.java','PackageCheck.java']],root/'tests/TlsChecks.java'])
        for name in ['ca','unrelated']:
            k=rsa.generate_private_key(public_exponent=65537,key_size=2048);n=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,name)])
            c=cert(name,k,n,k,ca=True);(work/(name+'.pem')).write_bytes(c.public_bytes(serialization.Encoding.PEM))
            if name=='ca':ca_key,ca_cert=k,c
        ports=[]
        for name,expired,host in [('valid',False,'localhost'),('expired',True,'localhost'),('wrong-host',False,'elsewhere.invalid')]:
            k=rsa.generate_private_key(public_exponent=65537,key_size=2048);c=cert(name,k,ca_cert.subject,ca_key,expired=expired,host=host)
            (work/(name+'.pem')).write_bytes(c.public_bytes(serialization.Encoding.PEM));(work/(name+'.key')).write_bytes(k.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
            server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.load_cert_chain(work/(name+'.pem'),work/(name+'.key'));server.socket=context.wrap_socket(server.socket,server_side=True)
            servers.append(server);ports.append(server.server_port);threading.Thread(target=server.serve_forever,daemon=True).start()
        run(['java','-cp',work,'dev.nemesiscatalog.TlsChecks','local',root/'assets/tls',work,*ports])
        if '--live' in sys.argv:
            run(['keytool','-importcert','-noprompt','-alias','unrelated','-file',work/'unrelated.pem','-keystore',work/'stale.p12','-storepass','fixture-only'])
            hello=next(m for m in json.loads((root/'module-catalog.json').read_text())['modules'] if m['id']=='catalog.hello')
            run(['java','-Djavax.net.ssl.trustStore='+str(work/'stale.p12'),'-Djavax.net.ssl.trustStorePassword=fixture-only','-cp',work,'dev.nemesiscatalog.TlsChecks','live',root/'assets/tls',hello['downloadUrl'],hello['bytes'],hello['sha256']])
    finally:
        for server in servers:server.shutdown();server.server_close()
