import os
import shutil
import subprocess

REMOVE_ALL_KERNELS = False

print("Finding out the package version...")
version = subprocess.check_output('rpmspec -q --queryformat="%{VERSION}\n" intel-media-driver-free.spec | head -1', shell=True)
version = version.decode("utf-8").strip()
print("Found %s" % version)

if not os.path.exists("intel-media-%s.tar.gz" % version):
    print("Source file not found, downloading...")
    os.system("wget https://github.com/intel/media-driver/archive/intel-media-%s.tar.gz" % version)

print("Unpacking...")
ret = os.system("tar -xf intel-media-%s.tar.gz" % version)

unpacked_dir = "media-driver-intel-media-%s" % version

print("Removing non-free kernels...")
ret = os.system("cd %s && find . -name kernel | grep gen | xargs rm -r" % unpacked_dir)
ret = os.system("cd %s && find . -name cm_gpucopy_kernel* | xargs rm" % unpacked_dir)
ret = os.system("cd %s && find . -name cmrt_kernel | xargs rm -r" % unpacked_dir)

if REMOVE_ALL_KERNELS:
    print("Removing free kernels...")
    ret = os.system("cd %s && find . -name kernel_free | grep gen | xargs git rm -r" % unpacked_dir)

print("Stripping non-free files and directories...")

print("Packing back up...")
os.system("tar -czf intel-media-%s-free.tar.gz %s" % (version, unpacked_dir))

print("Cleaning up...")
shutil.rmtree(unpacked_dir)

print("Done, created intel-media-%s-free.tar.gz" % version)
