import os, sys, binascii
from Scripts import ioreg, run, utils

class CheckNetwork:
    def __init__(self):
        self.u = utils.Utils("CheckNetwork")
        # Verify running OS
        if not sys.platform.lower() == "darwin":
            self.u.head("Wrong OS!")
            print("")
            print("This script can only be run on macOS!")
            print("")
            self.u.grab("Press [enter] to exit...")
            exit(1)
        self.r = run.Run()
        self.i = ioreg.IOReg()
        self.log = ""
        self.ioreg = None

    def get_boot_args(self):
        # Attempts to pull the boot-args from nvram
        out = self.r.run({"args":["nvram","-p"]})
        for l in out[0].split("\n"):
            if "boot-args" in l:
                return "\t".join(l.split("\t")[1:])
        return None

    def get_os_version(self):
        # Scrape sw_vers
        prod_name  = self.r.run({"args":["sw_vers","-productName"]})[0].strip()
        prod_vers  = self.r.run({"args":["sw_vers","-productVersion"]})[0].strip()
        build_vers = self.r.run({"args":["sw_vers","-buildVersion"]})[0].strip()
        if build_vers: build_vers = "({})".format(build_vers)
        return " ".join([x for x in (prod_name,prod_vers,build_vers) if x])

    def lprint(self, message):
        print(message)
        self.log += message + "\n"

    def main(self):
        self.u.head()
        self.lprint("")
        os_vers = self.get_os_version()
        self.lprint("Current OS Version: {}".format(os_vers or "Unknown!"))
        self.lprint("")
        boot_args = self.get_boot_args()
        self.lprint("Current boot-args: {}".format(boot_args or "None set!"))
        self.lprint("")
        self.lprint("Finding NICs...")
        all_devs = self.i.get_all_devices(plane="IOService")
        self.lprint("")
        self.lprint("Iterating for devices with matching class-code...")
        nics = [x for x in all_devs.values() if x.get("info",{}).get("class-code","").endswith("0200>")]
        if not nics:
            self.lprint(" - None found!")
            self.lprint("")
        else:
            self.lprint(" - Located {}".format(len(nics)))
            self.lprint("")
            self.lprint("Iterating NICs:")
            self.lprint("")
            for n in sorted(nics, key=lambda x:x.get("device_path","?")):
                n_dict = n.get("info",{})
                # Get the enX BSD Name - if possible
                name_check = "+-o {}  <class".format(n["name"])
                bsd_name = "Not Located"
                primed = False
                for line in self.i.get_ioreg():
                    if name_check in line:
                        primed = len(line.split("+-o ")[0])
                        continue
                    if primed is False:
                        continue
                    # We're primed check for "BSD Name" = "
                    # or if we left our scope
                    if "+-o " in line and len(line.split("+-o ")[0]) <= primed:
                        break
                    if '"BSD Name" = "' in line:
                        try:
                            bsd_name = line.split('"BSD Name" = "')[1].split('"')[0]
                        except:
                            pass
                        break
                loc = n.get("device_path")
                self.lprint(" - {} - {}".format(n["name"], loc or "Could Not Resolve Device Path"))
                try:
                    ven = "0x"+binascii.hexlify(binascii.unhexlify(n_dict["vendor-id"][1:5])[::-1]).decode().upper()
                except:
                    ven = "Not Located"
                try:
                    dev = "0x"+binascii.hexlify(binascii.unhexlify(n_dict["device-id"][1:5])[::-1]).decode().upper()
                except:
                    dev = "Not Located"
                self.lprint(" --> vendor-id {}".format(ven))
                self.lprint(" --> device-id {}".format(dev))
                self.lprint(" --> BSD Name  {}".format(bsd_name))
                self.lprint(" --> built-in  {}".format("YES" if "built-in" in n_dict or "IOBuiltin" in n_dict else "NO"))
                self.lprint(" --> Bridged   {}".format("NO" if "acpi-path" in n_dict else "YES - Needs to be defined in ACPI for DeviceProperties to work!"))
                self.lprint("")
        print("Saving log...")
        print("")
        os.chdir(os.path.dirname(os.path.realpath(__file__)))
        with open("NIC.log","w") as f:
            f.write(self.log)
        print("Done.")
        print("")

if __name__ == '__main__':
    a = CheckNetwork()
    a.main()
