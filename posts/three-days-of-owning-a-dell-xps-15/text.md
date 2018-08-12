# Three days of owning a Dell XPS 15 (9570)

> Apple might seriously change up it's MacBook Pro lineup [relatively soon](https://9to5mac.com/2018/04/03/arm-based-mac-opinion/) and High Sierra left a sour taste in my mouth, so I don't feel comfortable investing a decent chunk of money into a software and hardware ecosystem that is either going to deteriorate in quality even further or is going to be changing quite drastically in the near future. Either way, I needed a new laptop pronto, as my previous Mac is starting to show it's age. 

That's the situation lots of people, including me, are currently finding themselves in. My plan to escape this dilemma was simple: Buy a beefy and aesthetically pleasing Windows laptop, install my Linux distro of choice, and hope for the best when it comes to driver support. 

After lengthy research (and being influenced by HN comments) I finally decided to go with a [Dell XPS 15 (9570)]( https://www.dell.com/en-us/work/shop/dell-laptops-and-notebooks/new-xps-15/spd/xps-15-9570-laptop/cax15w10p1c1654p).

As you'll see, that plan didn't quite pan out the way I had hoped it would.

## Day 1

The laptop arrived at my home address after about two weeks in transit. Upon opening the cardboard box it came in, I was treated to a stench that no other electronics product purchase I ever made reeked of (a mix of cheap plastic and glue). Thankfully that unit itself was not suspect to the same smell.

### Hardware
<p align="center">
<img src="xps-15.png" width="500px" />
</p>
<figcaption>Dell XPS 15 (9570)</figcaption>

The design of the XPS series hasn't really changed much since the introduction of the InfinityEdge display back in 2015, and that's good for once because the understated look that the laptop is going for is definitely nice. It generally looks and feels premium. 

My particular unit exhibited noticeable backlight bleed on the bottom left and right corner of the screen. This problem seems to be [quite common](https://www.dell.com/community/XPS/9570-Acceptable-backlight-bleed/td-p/6091926), but Dell does at least offer replacements if **they** deem the backlight bleed unacceptable. Coil whine was also present, but I wasn't able to reproduce it consistently.

One-handed operation of the display hinge is definitely out of the question, as pressing down on the chassis is required to open up the laptop, but that's more of a minor nitpick than actual criticism.

### Initial setup

Before wiping the Windows partition I performed a "critical" [BIOS upgrade](https://www.dell.com/support/home/us/en/19/product-support/product/xps-15-9570-laptop/drivers).  Dell does upload firmware updates to the [Linux Vendor Firmware Service](https://fwupd.org/vendorlist) which can then be installed with [`fwupd`](https://github.com/hughsie/fwupd), but the most recent BIOS version (1.3.0) was not yet available at the time of writing.

With all that out of the way I was finally able to start the installation process of my Linux distribution of choice, which is Debian `testing ` — or so I thought.

The built-in Killer wireless networking adapter ([Qualcomm Atheros QCA6174](https://www.qualcomm.com/products/qca6174a-dual-band-wi-fi)) requires a non-free driver to operate, which in turn necessitates a [non-free Debian installer image](http://cdimage.debian.org/cdimage/unofficial/non-free/cd-including-firmware/). Additionally, I had to modify a slew of BIOS settings to successfully boot from a USB drive and subsequently install Debian.

* `Secure Boot → Secure Boot Enable → Uncheck`

  Only a few Linux distributions support Secure Boot, and Debian isn't one of them yet.

* `System Configuration → SATA Configuration → AHCI`

  Intel Rapid Storage isn't supported on Linux particularly well (at least out of the box). Configuring SATA for AHCI (Advanced Host Controller Interface) is necessary to make the Debian installer recognize the built-in NVMe drive.

* `System Configuration → Thunderbolt Auto Switch → Native Enumeration`

  I don't own any Thunderbolt devices, so I was unable to test the difference between  `Native Enumeration` and `BIOS Assist Enumeration`, but I disabled `Auto Switch` because the actual switching takes place every time the laptop powers on and therefor negatively impacts startup-time.

* `Intel(R) Software Guard Extensions → Intel(R) SGX Enable → Enabled`

  > **Intel SGX** is a set of central processing unit (CPU) instruction codes from **Intel** that allows user-level code to allocate private regions of memory, called enclaves, that are protected from processes running at higher privilege levels.

  "Sounds terrible and incredibly vague", I thought. So I disabled it and quickly realized that the built-in Killer wireless networking adapter vanished from `lspci`'s output. Don't disable it if you want to use WiFi, I guess.

After performing these changes, the Debian installation proceeded without any further interruptions.

After the installation was finished, I was presented with a completely empty boot order list. After lengthy troubleshooting I discovered that boot entries have to be added manually. **Why?**

<p align="center">
  <img src="boot-order.jpeg" width="400px" alt="Boot entry add dialog" />
</p>
<figcaption>Manually adding GRUB as a boot option</figcaption>

By that point it was already getting late and I decided to continue the next day.

## Day 2
With Debian installed it was time to run my [trusty setup scripts](https://github.com/PhilipTrauner/dotfiles) to make the machine feel like home, but issues arose pretty much immediately.

Installing any desktop environment / window manager (in my case `i3`) pulls in `xserver-xorg-video-nouveau` on Debian. After the first reboot, nothing seemed out of the ordinary, until my system froze up after about a minute of very light usage (sitting idle on the `lightdm` login screen).

Turns out that `nouveau` currently doesn't play well with the XPS 15's GTX 1050 Ti and also lacks the courtesy to crash early and predictably. To temporarily get the system up and running again, a simple `nomodeset` is not sufficient. Instead, `nouveau.modeset=0` has to be appended to the [kernel arguments](https://wiki.archlinux.org/index.php/kernel_parameters#GRUB). 

But that's just a temporary fix. Thankfully, there are still two other more longterm solutions remaining: 

1. Install the official NVIDIA drivers (*ugh*) and utilize `bumblebee` to switch between integrated and dedicated graphics.
2. Disable the dedicated graphics card outright by removing `xserver-xorg-video-nouveau`.

I went with the first option. My workflow isn't really enhanced by a dedicated graphics card, but because I involuntarily purchased the 1050 Ti I didn't want the money to go to waste, so I figured that I should at least setup `bumblebee` to be able to switch between both graphics solutions.

There's just one problem minor problem: `bbswitch`, which is what `bumblebee` uses to power down the graphics card when it is not in use, does not work properly on Linux 4.17. It claims that it does (`/proc/acpi/bbswitch` → `0000:01:00.0 OFF`), but digging around in sysfs (`/sys/class/pci_bus/0000:01/power/runtime_enabled` → `enabled`) and occasional fan spin-ups that are not tied to CPU usage tell us a different story. It also fails to properly power on the card when prompted to by `optirun` or `primusrun` (Although there appears to be a [partial fix](https://github.com/JackHack96/dell-xps-9570-ubuntu-respin) that forgoes `bbswitch` usage on startup). 

Surprisingly, upgrading to Linux 4.18-rc4 fixed the graphics card shutdown on boot, but now `bbswitch` re-enables the graphics card every time the computer leaves lid-sleep, upon which the card can not be shut down anymore. This effectively renders `bumblebee` useless and absolutely destroys battery life. `i3-bar` suggests a drop from 11 hours to just three.

```
bbswitch: loading out-of-tree module taints kernel.
bbswitch: version 0.8
bbswitch: Found integrated VGA device 0000:00:02.0: \_SB_.PCI0.GFX0
bbswitch: Found discrete VGA device 0000:01:00.0: \_SB_.PCI0.PEG0.PEGP
bbswitch: detected an Optimus _DSM function
bbswitch: disabling discrete graphic
```
<figcaption>dmesg output of bbswitch</figcaption>

As the troubleshooting commenced I was feeling less and less satisfied with my purchase decision. Thankfully, it was already getting late, which I used as an excuse to go to bed.

## Day 3
After some graphics card related nightmares I still had some fight left in me and continued on.

I wanted to tackle the lack of tap-to-click first, as it had already gotten on my nerves the day before. Debian utilizes `libinput` to handle input devices like touchpads. It performs admirably overall, although it is certainly lacking in the configuration department when compared to [`mtrack`](https://github.com/p2rkw/xf86-input-mtrack) and [`synaptics`](https://packages.debian.org/en/buster/xserver-xorg-input-synaptics). [Tap-to-click](https://wiki.archlinux.org/index.php/Libinput) can be enabled though, and from my experience it works significantly better than the two alternatives, as once enabled there is basically no pointer jitter. With all of that being said, I was still thoroughly disappointed as I was used to the excellent trackpad handling on macOS. It seems that [I'm not the only one feeling this way](https://news.ycombinator.com/item?id=17547817), but nobody has taken the initiative to do something about it yet.

Anyway, next I decided to look into ways to improve the abysmal battery life.
The ever helpful [Arch Linux Wiki](https://wiki.archlinux.org/index.php/Laptop) suggests a tool called [`tlp`](https://linrunner.de/en/tlp/tlp.html) specifically for ThinkPads, but nowadays it basically work on any laptop.

"Sounds great!", I thought, until I noticed that I was unable to establish WiFi connections after installing it. Even after a `apt-get purge tlp` the Killer wireless networking adapter stubbornly refused to participate in any key-exchanges. After rigorous troubleshooting I realized that `tlp` had pulled in `network-manager` without me noticing, which perfectly explains basically every kind of networking anomaly, as `network-manager` doesn't play well with `systemd-networkd`.

Another potential issue I avoided thanks to the Arch Linux Wiki was a conflict between `bbswitch` and the PCI power management functionality of `tlp`. The PCI address of the NVIDIA graphics card has to be excluded from `tlp`'s runtime power management, otherwise bad things might happen. 

```
# Exclude PCI(e) device adresses the following list from Runtime PM
# (separate with spaces). Use lspci to get the adresses (1st column).
RUNTIME_PM_BLACKLIST="01:00.0"
```
<figcaption>Appending the PCI address of the NVIDIA graphics card to the tlp runtime power management blacklist prevents a potential conflict with bbswitch</figcaption>

All things considering, I probably wouldn't have run into the issue in the first place as `bbswitch` still wasn't working properly anyway.

After another round of extensive troubleshooting with the goal of permanently disabling the graphics card I decided to give up. I scrubbed the drive, and contacted Dell support to arrange a refund. The support agent was very accommodating and I was surprised to find out that Dell even offers to send someone to retrieve the laptop for free. 

## Conclusion
If you can handle pretty terrible battery life, don't mind installing the closed-source NVIDIA graphics driver, want to carry around a mouse, can ignore the coil-whine and the backlight-bleed, and are willing to put in a few days to get everything up and running, then you probably won't regret your purchase. Otherwise the only solution I can offer you is to bite the bullet and buy another overpriced MacBook that thermal-throttles even worse than the XPS 15. Its what I did, and its also probably what you'll do too.