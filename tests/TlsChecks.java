package dev.nemesiscatalog;

import java.io.*;
import java.net.URL;
import java.security.cert.*;
import javax.net.ssl.*;

public final class TlsChecks {
    interface Attempt { void run()throws Exception; }
    static void rejects(Attempt a)throws Exception {try{a.run();throw new AssertionError("Invalid TLS peer accepted");}catch(SSLException expected){}}
    static X509TrustManager roots(String... paths)throws Exception {
        InputStream[] in=new InputStream[paths.length];
        try{for(int i=0;i<paths.length;i++)in[i]=new FileInputStream(paths[i]);return TlsTrust.supplemental(in);}
        finally{for(InputStream s:in)if(s!=null)s.close();}
    }
    static void request(int port,SSLSocketFactory factory)throws Exception {
        HttpsURLConnection c=(HttpsURLConnection)new URL("https://localhost:"+port+"/").openConnection();
        c.setSSLSocketFactory(factory);c.setConnectTimeout(5000);c.setReadTimeout(5000);
        try{if(c.getResponseCode()!=200)throw new AssertionError("Expected HTTP 200");try(InputStream in=c.getInputStream()){if(in.read()!=79)throw new AssertionError("Wrong body");}}finally{c.disconnect();}
    }
    public static void main(String[] args)throws Exception {
        String assets=args[1];X509TrustManager bundled=roots(assets+"/isrg-root-x1.pem",assets+"/usertrust-ecc.pem");
        if(args[0].equals("live")) {
            try(InputStream a=new FileInputStream(assets+"/isrg-root-x1.pem");InputStream b=new FileInputStream(assets+"/usertrust-ecc.pem")){Network.configureTrust(a,b);}
            String catalog=Network.catalog(false,Policy.CATALOG);if(!catalog.contains("apbreck/RepoMan"))throw new AssertionError("Wrong catalog");
            File zip=File.createTempFile("repoman-live-", ".zip");try{
                try(OutputStream out=new FileOutputStream(zip)){Network.fetch(args[2],out,Policy.MAX_DOWNLOAD,Long.parseLong(args[3]),false,null);}
                PackageCheck.verify(zip,"catalog.hello","1.0.0",args[4],Long.parseLong(args[3]));
            }finally{zip.delete();}
            System.out.println("PASS: real GitHub catalog + release redirect/download/hash, with unrelated simulated system CA store");return;
        }
        X509TrustManager unrelated=roots(args[2]+"/unrelated.pem"),fixture=roots(args[2]+"/ca.pem");
        SSLSocketFactory supplemented=TlsTrust.factory(TlsTrust.combine(unrelated,fixture));
        int valid=Integer.parseInt(args[3]),expired=Integer.parseInt(args[4]),wrong=Integer.parseInt(args[5]);
        request(valid,supplemented);
        request(valid,TlsTrust.factory(TlsTrust.combine(fixture,bundled))); // system trust still works
        rejects(()->request(valid,TlsTrust.factory(TlsTrust.combine(unrelated,bundled))));
        rejects(()->request(expired,supplemented));
        rejects(()->request(wrong,supplemented));
        try{TlsTrust.supplemental(new ByteArrayInputStream(new byte[0]));throw new AssertionError("Empty roots accepted");}catch(CertificateException expected){}
        System.out.println("PASS: supplemental and system roots accepted; untrusted, expired, wrong-host peers and empty roots rejected");
    }
}
