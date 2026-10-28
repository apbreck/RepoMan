#!/usr/bin/env python3
import pathlib,os,subprocess,zipfile,shutil,hashlib,json
root=pathlib.Path(__file__).resolve().parent
sdk=pathlib.Path(os.environ.get('ANDROID_HOME',str(pathlib.Path.home()/'Library/Android/sdk')))
bt=sdk/'build-tools/35.0.0';android=sdk/'platforms/android-35/android.jar'
build=pathlib.Path(os.environ.get('BROWSER_BUILD_DIR',str(root/'build')));keys=pathlib.Path(os.environ.get('BROWSER_SIGNING_DIR',str(root/'signing')));dist=root/'dist'
for p in [build,keys,dist]:p.mkdir(parents=True,exist_ok=True)
def run(a):subprocess.run([str(x) for x in a],check=True)
classes=build/'classes';tests=build/'tests';dex=build/'dex'
for p in [classes,tests,dex]:p.mkdir(exist_ok=True)
run(['javac','--release','8','-classpath',android,'-d',classes,*sorted((root/'src').rglob('*.java'))])
run(['javac','-d',tests,root/'src/dev/nemesiscatalog/Policy.java',root/'src/dev/nemesiscatalog/PackageCheck.java',root/'tests/ChecksTest.java'])
run(['java','-cp',tests,'ChecksTest'])
run([bt/'d8','--min-api','19','--lib',android,'--output',dex,*sorted(classes.rglob('*.class'))])
unsigned=build/'unsigned.apk';run([bt/'aapt','package','-f','-M',root/'AndroidManifest.xml','-A',root/'assets','-I',android,'-F',unsigned])
with zipfile.ZipFile(unsigned,'a',zipfile.ZIP_DEFLATED) as z:z.write(dex/'classes.dex','classes.dex')
aligned=build/'aligned.apk';run([bt/'zipalign','-f','4',unsigned,aligned])
key=keys/'module-browser.p12'
if not key.exists():run(['keytool','-genkeypair','-keystore',key,'-storetype','PKCS12','-storepass','local-browser','-keypass','local-browser','-alias','browser','-keyalg','RSA','-keysize','2048','-validity','3650','-dname','CN=Local RepoMan'])
apk=dist/'RepoMan.apk'
run([bt/'apksigner','sign','--ks',key,'--ks-key-alias','browser','--ks-pass','pass:local-browser','--min-sdk-version','19','--v1-signing-enabled','true','--out',apk,aligned])
run([bt/'apksigner','verify','--min-sdk-version','19','--max-sdk-version','19',apk])
stage=build/'stage'
if stage.exists():shutil.rmtree(stage)
shutil.copytree(root/'package',stage);(stage/'app').mkdir();shutil.copy2(apk,stage/'app/RepoMan.apk')
with zipfile.ZipFile(stage/'install-gate.jar','w',zipfile.ZIP_DEFLATED) as z:z.write(dex/'classes.dex','classes.dex')
for n in ['LICENSE','THIRD_PARTY_NOTICES.md']:shutil.copy2(root/n,stage/n)
def pack(folder,out):
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(folder.rglob('*')):
   if p.is_file():z.write(p,str(p.relative_to(folder)))
module=dist/'repoman-0.1.2.zip';pack(stage,module)
with zipfile.ZipFile(dist/'repoman-0.1.2-usb.zip','w',zipfile.ZIP_DEFLATED) as z:
 z.writestr('NEMESIS.data','[nemesis]\nversion=1\ntype=install\npath=packages/repoman.zip\n');z.write(module,'packages/repoman.zip');z.write(root/'README.md','REPOMAN-README.md');z.write(root/'LICENSE','LICENSE')
hello=dist/'catalog-hello-1.0.0.zip';pack(root/'hello',hello)
with zipfile.ZipFile(hello,'a',zipfile.ZIP_DEFLATED) as z:z.write(root/'LICENSE','LICENSE')
def entry(path,**fields):return dict(fields,bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
entries=[entry(hello,id='catalog.hello',name='Catalog Hello Test',version='1.0.0',publisher='apbreck',description='Tests downloading and installing a module. Writes one installed.txt marker inside its own package directory. No vehicle settings or services are changed.',compatibility='Experimental package-manager test. Requires NEMESIS. Physical-car installation has not been verified.',firmwarePrefixes=[],downloadUrl='https://github.com/apbreck/RepoMan/releases/download/v0.1.1/catalog-hello-1.0.0.zip')]
# Preserve other catalog entries; building the browser does not require their binaries locally.
catalog=root/'module-catalog.json'
if catalog.exists():
 existing=json.loads(catalog.read_text())
 entries.extend(m for m in existing.get('modules',[]) if m['id']!='catalog.hello')
catalog.write_text(json.dumps(dict(schemaVersion=1,repository='apbreck/RepoMan',modules=entries),indent=2)+'\n')
with open(dist/'SHA256SUMS.txt','w') as f:
 for p in [module,dist/'repoman-0.1.2-usb.zip',hello]:f.write(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n')
print('Built browser and test catalog:',dist)
