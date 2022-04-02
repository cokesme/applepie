import os, subprocess, shutil, threading, time, sys

print("Checking for cl.exe... ", end='', flush=True)
assert b"Microsoft (R) C/C++ Optimizing Compiler" in subprocess.check_output(["cl.exe", "/?"], stderr=subprocess.STDOUT)
print("ok")

print("Checking that cl.exe is for x64... ", end='', flush=True)
assert b"for x64" in subprocess.check_output(["cl.exe", "/?"], stderr=subprocess.STDOUT)
print("ok")

# TODO select the correct bash exe
# Wsl is enabled in pipelines, but it is wsl1
# Windows Subsystem for Linux [WSLv1]
# https://github.com/actions/virtual-environments/blob/main/images/win/Windows2022-Readme.md
bash = "C:\\Windows\\System32\\bash.exe"

if len(sys.argv) == 2 and sys.argv[1] == "deepclean":
    # Completely clean box, including cleaning makefiles from autoconf
    if os.path.exists("bochs_build"):
        shutil.rmtree("bochs_build")
    os.chdir("bochservisor")
    subprocess.check_call(["cargo", "clean"])
    os.chdir("..")
elif len(sys.argv) == 2 and sys.argv[1] == "bochsclean":
# Completely clean box, including cleaning makefiles from autoconf
    if os.path.exists("bochs_build"):
        shutil.rmtree("bochs_build")
elif len(sys.argv) == 2 and sys.argv[1] == "clean":
    # Clean objects and binaries
    os.chdir("bochs_build")
    subprocess.check_call([bash, "-c", "make all-clean"])
    os.chdir("..")
    os.chdir("bochservisor")
    subprocess.check_call(["cargo", "clean"])
    os.chdir("..")
else:
    # Build bochservisor
    os.chdir("bochservisor")
    subprocess.check_call(["cargo", "build", "--release"])
    os.chdir("..")

    # Go into bochs build directory
    if not os.path.exists("bochs_build"):
        os.mkdir("bochs_build")
    os.chdir("bochs_build")

    # Set the compiler and linker to MSVC. Without this the ./configure script will
    # potentially use GCC which would result in things like "unsigned long" being
    # reported as 8 bytes instead of the 4 bytes they are on Windows
    os.environ["CC"] = "cl.exe"
    os.environ["CXX"] = "cl.exe"
    os.environ["LD"] = "link.exe"
    os.environ["LIBTOOL"] = "lib.exe"
    os.environ["WSLENV"]="LD/u:CXX/u:CC/u:LIBTOOL/u"
    #subprocess.run([bash], shell=True, env=os.environ)
    # If we have not configured bochs before, or if the configure script is newer
    # than the last configure, reconfigure
    if not os.path.exists("bochs_configured") or os.path.getmtime("bochs_configured") < os.path.getmtime("../bochs_config"):
        # Configure bochs
        subprocess.check_call([bash, "../bochs_config"], env=os.environ)

        # Create a marker indicating that bochs is configured
        with open("bochs_configured", "wb") as fd:
            fd.write(b"WOO")
    else:
        print("Skipping configuration as it's already up to date!")

    # Build bochs
    subprocess.check_call([bash, "-c", "time make -s -j16"], env=os.environ)
    os.chdir("..")
