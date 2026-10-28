package dev.nemesiscatalog;

import java.io.InputStream;
import java.security.KeyStore;
import java.security.cert.*;
import java.util.*;
import javax.net.ssl.*;

/** Adds issuer roots to this app only; certificate validation remains mandatory. */
final class TlsTrust {
    static X509TrustManager manager(KeyStore store)throws Exception {
        TrustManagerFactory f=TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm());
        f.init(store);
        for(TrustManager m:f.getTrustManagers())if(m instanceof X509TrustManager)return (X509TrustManager)m;
        throw new CertificateException("No X509 trust manager available");
    }
    static X509TrustManager supplemental(InputStream... roots)throws Exception {
        KeyStore store=KeyStore.getInstance(KeyStore.getDefaultType());store.load(null,null);
        CertificateFactory certificates=CertificateFactory.getInstance("X.509");int count=0;
        for(InputStream in:roots)for(java.security.cert.Certificate c:certificates.generateCertificates(in)) {
            X509Certificate root=(X509Certificate)c;
            root.checkValidity();
            if(root.getBasicConstraints()<0||!root.getSubjectX500Principal().equals(root.getIssuerX500Principal()))throw new CertificateException("Expected a self-signed CA root");
            root.verify(root.getPublicKey());store.setCertificateEntry("root-"+(count++),root);
        }
        if(count==0)throw new CertificateException("No supplemental CA roots");
        return manager(store);
    }
    static X509TrustManager combine(final X509TrustManager system,final X509TrustManager extra) {
        return new X509TrustManager(){
            public void checkServerTrusted(X509Certificate[] chain,String auth)throws CertificateException {
                if(chain==null||chain.length==0)throw new CertificateException("Missing server certificate");
                chain[0].checkValidity();
                try{system.checkServerTrusted(chain,auth);}catch(CertificateException original){
                    try{extra.checkServerTrusted(chain,auth);}catch(CertificateException failure){throw new CertificateException("Server certificate is not trusted by the device or RepoMan CA roots",failure);}
                }
            }
            public void checkClientTrusted(X509Certificate[] chain,String auth)throws CertificateException{system.checkClientTrusted(chain,auth);}
            public X509Certificate[] getAcceptedIssuers(){
                List<X509Certificate> all=new ArrayList<X509Certificate>();Collections.addAll(all,system.getAcceptedIssuers());Collections.addAll(all,extra.getAcceptedIssuers());return all.toArray(new X509Certificate[0]);
            }
        };
    }
    static SSLSocketFactory factory(X509TrustManager manager)throws Exception {
        SSLContext context=SSLContext.getInstance("TLS");context.init(null,new TrustManager[]{manager},null);return context.getSocketFactory();
    }
}
