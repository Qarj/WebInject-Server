import subprocess

result = subprocess.run(["perl", "..\WebImblaze-Framework\wif.pl", "..\WebImblaze\examples\get.xml"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
print ("Args:", result.args)
print (result.stdout.decode())
print ("Return Code:", result.returncode)
